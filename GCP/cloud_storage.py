import os
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
import logging

from google.cloud import storage


PROJECT_ID = 'df-backend'
BUCKET_NAME = 'df-backend'
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)
max_workers = 4


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


def _upload_file(local_path: str, gcs_path: str) -> bool:
    try:
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
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


def upload_directory(local_dir: str, gcs_base_path: str) -> Tuple[int, int]:
    local_dir = os.path.abspath(local_dir)
    local_dir_parent = os.path.dirname(local_dir)
    all_files = _get_all_files(local_dir)
    total_files = len(all_files)
    
    if total_files == 0:
        logger.warning(f"No files found in {local_dir}")
        return 0, 0

    logger.info(f"Starting upload of {total_files} files from {local_dir}")
    upload_tasks = []
    for local_path in all_files:
        relative_path = os.path.relpath(local_path, local_dir_parent)
        gcs_path = os.path.join(gcs_base_path, relative_path)
        gcs_path = gcs_path.replace('\\', '/')
        upload_tasks.append((local_path, gcs_path))

    successful_uploads = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_upload_file, local_path, gcs_path)
            for local_path, gcs_path in upload_tasks
        ]
        for future in futures:
            if future.result():
                successful_uploads += 1

    logger.info(
        f"Upload completed: {successful_uploads}/{total_files} files successful"
    )
    return successful_uploads, total_files


def download_directory(gcs_base_path: str, local_dir: str) -> Tuple[int, int]:
    try:
        blobs = list(bucket.list_blobs(prefix=gcs_base_path))
        total_files = len(blobs)
        if total_files == 0:
            logger.warning(f"No files found in gs://{bucket.name}/{gcs_base_path}")
            return 0, 0
        logger.info(f"Starting download of {total_files} files to {local_dir}")
        os.makedirs(local_dir, exist_ok=True)
        successful_downloads = 0
        for blob in blobs:
            relative_path = os.path.relpath(blob.name, gcs_base_path)
            local_path = os.path.join(local_dir, relative_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            try:
                blob.download_to_filename(local_path)
                successful_downloads += 1
                logger.info(f"Downloaded: {blob.name} -> {local_path}")
            except Exception as e:
                logger.error(f"Error downloading {blob.name}: {str(e)}")
        logger.info(
            f"Download completed: {successful_downloads}/{total_files} files successful"
        )
        return successful_downloads, total_files

    except Exception as e:
        logger.error(f"Error in download_directory: {str(e)}")
        return 0, 0
    

def download_file(gcs_path: str, local_path: str) -> bool:
    try:
        blob = bucket.blob(gcs_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
        logger.info(f"Downloaded: {gcs_path} -> {local_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading {gcs_path}: {str(e)}")
        return False