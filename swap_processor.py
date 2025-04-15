import os
import shutil
import argparse
import asyncio

import GCP.cloud_storage as cs
import DeepFake.core.swap as swap
import DeepFake.utils.filesystem as filesystem


# def parse_arguments():
#     parser = argparse.ArgumentParser(description='Process video')
#     parser.add_argument('--user_dir', type=str, help='Cloud path to user directory')
#     parser.add_argument('--video_dir', type=str, help='Cloud path to video')
#     args = parser.parse_args()
#     return args


# async def run():
#     args = parse_arguments()
#     user_dir = args.user_dir
#     cloud_video_dir = args.video_dir
#     cloud_source_dir = user_dir + '/source'
#     cloud_embeddnig_dir = user_dir + '/output/embedding'
#     temp_dir = filesystem.resolve_relative_path('./temp')
#     local_user_dir = temp_dir + '/' + cloud_source_dir.split('/')[-2]
#     local_source_dir = local_user_dir + '/source'
#     local_embeddnig_dir = local_user_dir + '/output/embedding'
#     local_video_dir = local_user_dir + '/' + cloud_video_dir.split('/')[-1]
#     local_target_dir = local_video_dir + '/output'
#     local_output_dir = local_user_dir + '/output'
#     original_video_path = os.path.join(local_video_dir, cloud_video_dir.split('/')[-1] + '.mp4')
#     upload_output_dir = filesystem.get_parent_dir(cloud_source_dir)
#     try:
#         await cs.download_directory(cloud_source_dir, local_source_dir)
#         await cs.download_directory(cloud_embeddnig_dir, local_embeddnig_dir)
#         await cs.download_directory(cloud_video_dir, local_video_dir)
#         swap.run(local_source_dir, local_target_dir, local_output_dir, original_video_path)
#         await cs.upload_directory(local_output_dir, upload_output_dir)
#     except:
#         raise
#     shutil.rmtree(local_user_dir)


# if __name__ == "__main__":
#     asyncio.run(run())


async def run(user_dir: str, cloud_video_dir: str):
    cloud_source_dir = user_dir + '/source'
    cloud_embeddnig_dir = user_dir + '/output/embedding'
    temp_dir = filesystem.resolve_relative_path('./temp')
    local_user_dir = temp_dir + '/' + cloud_source_dir.split('/')[-2]
    local_source_dir = local_user_dir + '/source'
    local_embeddnig_dir = local_user_dir + '/output/embedding'
    local_video_dir = local_user_dir + '/' + cloud_video_dir.split('/')[-1]
    local_target_dir = local_video_dir + '/output'
    local_output_dir = local_user_dir + '/output'
    original_video_path = os.path.join(local_video_dir, cloud_video_dir.split('/')[-1] + '.mp4')
    upload_output_dir = filesystem.get_parent_dir(cloud_source_dir)
    try:
        await cs.download_directory(cloud_source_dir, local_source_dir)
        await cs.download_directory(cloud_embeddnig_dir, local_embeddnig_dir)
        await cs.download_directory(cloud_video_dir, local_video_dir)
        swap.run(local_source_dir, local_target_dir, local_output_dir, original_video_path)
        await cs.upload_directory(local_output_dir, upload_output_dir)
    except:
        raise
    shutil.rmtree(local_user_dir)