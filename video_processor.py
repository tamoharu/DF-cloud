import os
import shutil
import argparse

import GCP.cloud_storage as cs
import DeepFake.core.mask as mask
import DeepFake.utils.filesystem as filesystem


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process video')
    parser.add_argument('--video_path', type=str, help='Cloud path to video')
    args = parser.parse_args()
    return args


def run():
    args = parse_arguments()
    cloud_video_path = args.video_path
    video_name = cloud_video_path.split('/')[-1]
    temp_dir = filesystem.resolve_relative_path('./temp')
    local_video_dir = temp_dir + '/' + video_name.split('.')[0]
    local_video_path = os.path.join(local_video_dir, video_name)
    local_output_dir = local_video_dir + '/' + 'output'
    cloud_video_dir = '/'.join(cloud_video_path.split('/')[:-1])
    try:
        cs.download_file(cloud_video_path, local_video_path)
        mask.run(local_video_path, local_output_dir)
        cs.upload_directory(local_output_dir, cloud_video_dir)
    except:
        raise
    shutil.rmtree(local_video_dir)


if __name__ == '__main__':
    run()