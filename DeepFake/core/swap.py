import os
from typing import List
import glob

import cv2
import numpy as np

import DeepFake.config.type as type
import DeepFake.config.globals as globals
import DeepFake.config.words as words
import DeepFake.utils.log as log
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.vision as vision
import DeepFake.utils.ffmpeg as ffmpeg
import DeepFake.utils.swap_util as swap_util
import DeepFake.utils.multi_process as multi_process
import DeepFake.core.model_zoo.arcface_inswapper as embedder
import DeepFake.core.model_zoo.inswapper as swapper


def run(source_frame_dir: str, target_face_dir: str, output_dir: str, original_video_path: str) -> None:
    source_frame_paths = sorted(glob.glob(os.path.join(source_frame_dir, '*')))
    source_frames = vision.read_static_images(source_frame_paths)
    temp_dir = output_dir + globals.TEMP_DIR
    target_frame_dir = target_face_dir + globals.FRAME_DIR
    swapped_dir = output_dir + globals.SWAPPED_FRAME_DIR
    parent_dir = filesystem.get_parent_dir(original_video_path)
    source_embedding_path = filesystem.get_save_path(output_dir, globals.SOURCE_EMBEDDING_DIR, parent_dir, globals.EMBEDDING_EXTENSION)
    output_path = filesystem.get_save_path(output_dir, '/', original_video_path, globals.VIDEO_EXTENSION)
    temp_output_path = filesystem.get_save_path(output_dir, globals.TEMP_DIR, original_video_path, globals.VIDEO_EXTENSION)
    frame_paths = sorted(glob.glob(os.path.join(target_frame_dir, '*')))
    if not filesystem.is_file(source_embedding_path):
        create_source_embedding(source_frames, source_embedding_path)
    multi_process.run(process_frames, frame_paths, source_embedding_path, target_face_dir, output_dir)
    if not ffmpeg.merge_video(swapped_dir, temp_output_path, globals.VIDEO_FPS):
        log.error(words.get('swap/merge_video'), __name__.upper())
    if not ffmpeg.restore_audio(original_video_path, temp_output_path, output_path):
        log.error(words.get('swap/restore_audio'), __name__.upper())
        filesystem.move_file(temp_output_path, output_path)
    filesystem.clear_directory(swapped_dir)
    filesystem.clear_directory(temp_dir)


def process_frames(update_progress: type.UpdateProcess, frame_paths: List[str], *args: str) -> None:
    source_embedding_path, target_face_dir, output_dir = args
    source_embedding = np.load(source_embedding_path)
    target_crop_frame_dir = target_face_dir + globals.CROP_FRAME_DIR
    target_mask_dir = target_face_dir + globals.MASK_DIR
    target_matrix_dir = target_face_dir + globals.MATRIX_DIR
    for frame_path in frame_paths:
        frame_name = os.path.basename(frame_path).split('.')[0]
        frame = vision.read_static_image(frame_path)
        face_pattern = f"{frame_name}_*"
        crop_face_paths = sorted(glob.glob(os.path.join(target_crop_frame_dir, face_pattern)))
        for crop_face_path in crop_face_paths:
            frame_face_id = os.path.basename(crop_face_path).split('.')[0]
            matrix_path = os.path.join(target_matrix_dir, frame_face_id + globals.MATRIX_EXTENSION)
            mask_path = os.path.join(target_mask_dir, frame_face_id + globals.MASK_EXTENSION)
            crop_frame = vision.read_static_image(crop_face_path)
            matrix = np.load(matrix_path)
            mask = np.load(mask_path)
            swapped_frame = swap(source_embedding, frame, crop_frame, matrix, mask)
            output_path = filesystem.get_save_path(output_dir, globals.SWAPPED_FRAME_DIR, frame_path, globals.FRAME_EXTENSION)
            vision.write_image(output_path, swapped_frame)
        update_progress()


def swap(source_embedding: type.Embedding, target_frame: type.Frame, target_crop_frame: type.Frame, target_matrix: type.Matrix, target_mask: type.Mask) -> type.Frame:
    swapped_crop_frame = swapper.run(target_crop_frame, source_embedding)
    temp_frame_size = target_frame.shape[:2][::-1]
    inverse_crop_frame = cv2.warpAffine(swapped_crop_frame, target_matrix, temp_frame_size, borderMode = cv2.BORDER_REPLICATE)
    paste_frame = target_frame.copy()
    paste_frame[:, :, 0] = target_mask * inverse_crop_frame[:, :, 0] + (1 - target_mask) * target_frame[:, :, 0]
    paste_frame[:, :, 1] = target_mask * inverse_crop_frame[:, :, 1] + (1 - target_mask) * target_frame[:, :, 1]
    paste_frame[:, :, 2] = target_mask * inverse_crop_frame[:, :, 2] + (1 - target_mask) * target_frame[:, :, 2]
    return paste_frame


def create_source_embedding(source_frames: List[type.Frame], output_path) -> None:
    source_embedding_list = []
    for source_frame in source_frames:
        source_crop_frame, _ = swap_util.crop_frame(source_frame, embedder.MODEL_SIZE, embedder.MODEL_TEMPLATE)
        source_embedding = embedder.run(source_crop_frame[0])
        source_embedding_list.append(source_embedding)
    mean_embedding = np.mean(source_embedding_list, axis=0)
    np.save(output_path, mean_embedding)