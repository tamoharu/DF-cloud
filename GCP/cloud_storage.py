import os
from typing import List, Tuple
import logging
import asyncio
import aiofiles

from google.cloud import storage


PROJECT_ID = 'df-backend'
BUCKET_NAME = 'df-backend'
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)
max_workers = 100

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


async def _upload_file(local_path: str, gcs_path: str) -> bool:
    try:
        blob = bucket.blob(gcs_path)
        if local_path.lower().endswith('.mp4'):
            async with aiofiles.open(local_path, 'rb') as f:
                file_data = await f.read()
                blob.content_type = 'video/mp4'
                await asyncio.to_thread(blob.upload_from_string, file_data, content_type='video/mp4')
        else:
            await asyncio.to_thread(blob.upload_from_filename, local_path)
            
        logger.info(f"Uploaded: {local_path} -> {gcs_path}")
        return True
    except Exception as e:
        logger.error(f"Error uploading {local_path}: {str(e)}")
        return False


def _get_all_files(local_dir: str) -> List[str]:
    all_files = []
    for root, _, files in os.walk(local_dir):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files


async def upload_directory(local_dir: str, gcs_base_path: str) -> Tuple[int, int]:
    local_dir = os.path.abspath(local_dir)
    local_dir_parent = os.path.dirname(local_dir)
    all_files = _get_all_files(local_dir)
    total_files = len(all_files)
    
    if total_files == 0:
        logger.warning(f"No files found in {local_dir}")
        return 0, 0

    logger.info(f"Starting upload of {total_files} files from {local_dir}")
    upload_tasks = []
    
    semaphore = asyncio.Semaphore(max_workers)
    
    async def upload_with_semaphore(local_path: str, gcs_path: str) -> bool:
        async with semaphore:
            return await _upload_file(local_path, gcs_path)
    
    for local_path in all_files:
        relative_path = os.path.relpath(local_path, local_dir_parent)
        gcs_path = os.path.join(gcs_base_path, relative_path)
        gcs_path = gcs_path.replace('\\', '/')
        task = upload_with_semaphore(local_path, gcs_path)
        upload_tasks.append(task)

    results = await asyncio.gather(*upload_tasks)
    successful_uploads = sum(1 for result in results if result)

    logger.info(
        f"Upload completed: {successful_uploads}/{total_files} files successful"
    )
    return successful_uploads, total_files


async def download_directory(gcs_base_path: str, local_dir: str) -> Tuple[int, int]:
    try:
        blobs = await asyncio.to_thread(lambda: list(bucket.list_blobs(prefix=gcs_base_path)))
        total_files = len(blobs)
        if total_files == 0:
            logger.warning(f"No files found in gs://{bucket.name}/{gcs_base_path}")
            return 0, 0
            
        logger.info(f"Starting download of {total_files} files to {local_dir}")
        os.makedirs(local_dir, exist_ok=True)
        semaphore = asyncio.Semaphore(max_workers)
        async def download_blob(blob) -> bool:
            async with semaphore:
                try:
                    if blob.name.endswith('/'):
                        return True
                    relative_path = os.path.relpath(blob.name, gcs_base_path)
                    local_path = os.path.join(local_dir, relative_path)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    await asyncio.to_thread(blob.download_to_filename, local_path)
                    logger.info(f"Downloaded: {blob.name} -> {local_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error downloading {blob.name}: {str(e)}")
                    return False

        download_tasks = [download_blob(blob) for blob in blobs]
        results = await asyncio.gather(*download_tasks)
        successful_downloads = sum(1 for result in results if result)

        logger.info(
            f"Download completed: {successful_downloads}/{total_files} files successful"
        )
        return successful_downloads, total_files

    except Exception as e:
        logger.error(f"Error in download_directory: {str(e)}")
        return 0, 0


async def download_file(gcs_path: str, local_path: str) -> bool:
    try:
        blob = bucket.blob(gcs_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        await asyncio.to_thread(blob.download_to_filename, local_path)
        logger.info(f"Downloaded: {gcs_path} -> {local_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading {gcs_path}: {str(e)}")
        return False