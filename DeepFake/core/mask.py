from typing import List, Tuple

import cv2
import numpy as np

import DeepFake.config.type as type
import DeepFake.config.globals as globals
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.swap_util as swap_util
import DeepFake.utils.ffmpeg as ffmpeg
import DeepFake.utils.vision as vision
import DeepFake.utils.multi_process as multi_process
import DeepFake.core.model_zoo.face_occluder as masker
import DeepFake.core.model_zoo.inswapper as swapper


def run(video_path: str, output_path: str):
    filesystem.clear_temp(video_path)
    filesystem.create_temp(video_path)
    target_video_resolution = vision.detect_video_resolution(video_path)
    output_video_resolution = vision.pack_resolution(target_video_resolution)
    ffmpeg.extract_frames(video_path, output_video_resolution, globals.VIDEO_FPS)
    frame_paths = filesystem.get_temp_frame_paths(video_path)
    multi_process.run(process_frames, frame_paths, output_path)


def process_frames(update_progress: type.UpdateProcess, frame_paths: List[str], *args: str) -> None:
    output_path = args[0]
    for frame_path in frame_paths:
        frame = vision.read_static_image(frame_path)
        mask_list, crop_frame_list, affine_matrix_list = mask_target(frame)
        idx = 0
        for mask, crop_frame, affine_matrix in zip(mask_list, crop_frame_list, affine_matrix_list):
            inverse_matrix = cv2.invertAffineTransform(affine_matrix)
            temp_frame_size = frame.shape[:2][::-1]
            inverse_crop_mask = cv2.warpAffine(mask, inverse_matrix, temp_frame_size).clip(0, 1)
            crop_frame_save_path = filesystem.get_save_path(output_path, globals.CROP_FRAME_DIR, frame_path, globals.FRAME_EXTENSION, idx)
            mask_save_path = filesystem.get_save_path(output_path, globals.MASK_DIR, frame_path, globals.MASK_EXTENSION, idx)
            matrix_save_path = filesystem.get_save_path(output_path, globals.MATRIX_DIR, frame_path, globals.MATRIX_EXTENSION, idx)
            vision.write_image(crop_frame_save_path, crop_frame)
            np.save(mask_save_path, inverse_crop_mask)
            np.save(matrix_save_path, inverse_matrix)
            idx += 1
        frame_save_path = filesystem.get_save_path(output_path, globals.FRAME_DIR, frame_path, globals.FRAME_EXTENSION)
        vision.write_image(frame_save_path, frame)
        update_progress()



def mask_target(target_frame: type.Frame) -> Tuple[List[type.Mask], List[type.Frame], List[type.Matrix]]:
    cropped_frames, affine_matrices = swap_util.crop_frame(target_frame, swapper.MODEL_SIZE, swapper.MODEL_TEMPLATE)
    if len(cropped_frames) == 0:
        return [], [], []
    mask_list = []
    for cropped_frame in cropped_frames:
        mask = masker.run(cropped_frame)
        mask_list.append(mask)
    return mask_list, cropped_frames, affine_matrices