from typing import List, Optional
import glob
import os
import shutil
import tempfile
from pathlib import Path
import inspect

import filetype

import DeepFake.config.globals as globals


TEMP_DIRECTORY_PATH = os.path.join(tempfile.gettempdir(), globals.PJ_NAME)
TEMP_OUTPUT_VIDEO_NAME = 'temp.mp4'
TEMP_OUTPUT_IMAGE_NAME = 'temp' + globals.FRAME_EXTENSION


def get_save_path(parent_dir: str, dir_name: str, file_path: str, extension: str, idx=None) -> str:
	name = os.path.basename(file_path).split('.')[0]
	output_dir = parent_dir + dir_name
	if not is_directory(output_dir):
		os.makedirs(output_dir)
	if idx is None:
		return output_dir + '/' + name + extension
	return output_dir + '/' + name + '_' + str(idx).zfill(3) + extension


def get_parent_dir(path):
   parts = path.rstrip("/\\").split("/")
   return "/".join(parts[:-1])


def get_temp_frame_paths(target_path: str) -> List[str]:
	temp_frames_pattern = get_temp_frames_pattern(target_path, '*')
	return sorted(glob.glob(temp_frames_pattern))


def get_temp_frames_pattern(target_path: str, temp_frame_prefix: str) -> str:
	temp_directory_path = get_temp_directory_path(target_path)
	return os.path.join(temp_directory_path, temp_frame_prefix + globals.FRAME_EXTENSION)


def get_temp_directory_path(target_path: str) -> str:
	target_name, _ = os.path.splitext(os.path.basename(target_path))
	return os.path.join(TEMP_DIRECTORY_PATH, target_name)


def get_temp_output_video_path(target_path: str) -> str:
	temp_directory_path = get_temp_directory_path(target_path)
	os.path.basename(target_path) 
	return os.path.join(temp_directory_path, TEMP_OUTPUT_VIDEO_NAME)


def get_temp_output_image_path(target_path: str) -> str:
	temp_directory_path = get_temp_directory_path(target_path)
	return os.path.join(temp_directory_path, TEMP_OUTPUT_IMAGE_NAME)


def create_temp(target_path: str) -> None:
	temp_directory_path = get_temp_directory_path(target_path)
	Path(temp_directory_path).mkdir(parents = True, exist_ok = True)


def move_temp(target_path: str, output_path: str) -> None:
	temp_output_video_path = get_temp_output_video_path(target_path)
	if is_file(temp_output_video_path):
		if is_file(output_path):
			os.remove(output_path)
		shutil.move(temp_output_video_path, output_path)


def move_file(target_path: str, output_path: str) -> None:
	if is_file(target_path):
		if is_file(output_path):
			os.remove(output_path)
		shutil.move(target_path, output_path)


def clear_temp(target_path: str) -> None:
	temp_directory_path = get_temp_directory_path(target_path)
	parent_directory_path = os.path.dirname(temp_directory_path)
	if is_directory(temp_directory_path):
		shutil.rmtree(temp_directory_path)
	if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
		os.rmdir(parent_directory_path)


def clear_directory(directory_path: str) -> None:
	if is_directory(directory_path):
		shutil.rmtree(directory_path)


def is_file(file_path: str) -> bool:
	return bool(file_path and os.path.isfile(file_path))


def is_directory(directory_path: str) -> bool:
	return bool(directory_path and os.path.isdir(directory_path))


def is_image(image_path: str) -> bool:
	if is_file(image_path):
		return filetype.helpers.is_image(image_path)
	return False


def are_images(image_paths: List[str]) -> bool:
	if image_paths:
		return all(is_image(image_path) for image_path in image_paths)
	return False


def is_video(video_path: str) -> bool:
	if is_file(video_path):
		return filetype.helpers.is_video(video_path)
	return False


def resolve_relative_path(path: str) -> str:
    caller_frame = inspect.currentframe().f_back # type: ignore
    caller_path = caller_frame.f_code.co_filename # type: ignore
    caller_dir = os.path.dirname(os.path.abspath(caller_path))
    return os.path.abspath(os.path.join(caller_dir, path))


def list_directory(directory_path: str) -> Optional[List[str]]:
	if is_directory(directory_path):
		files = os.listdir(directory_path)
		return [ Path(file).stem for file in files if not Path(file).stem.startswith(('.', '__')) ]
	return None
