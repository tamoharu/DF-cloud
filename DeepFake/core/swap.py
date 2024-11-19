import os
from typing import List

import cv2
import numpy as np

import DeepFake.config.type as type
import DeepFake.config.globals as globals
import DeepFake.utils.vision as vision
import DeepFake.core.model_zoo.arcface_inswapper as embedder
import DeepFake.core.model_zoo.inswapper as swapper
import DeepFake.utils.swap_util as swap_util


def process_frames(source_frames: List[type.Frame], source_embedding_path: str, target_face_dir: str) -> None:
    source_embedding = np.load(source_embedding_path)
    target_frame_dir = target_face_dir + globals.FRAME_DIR
    target_crop_frame_dir = target_face_dir + globals.CROP_FRAME_DIR
    target_mask_dir = target_face_dir + globals.MASK_DIR
    target_matrix_dir = target_face_dir + globals.MATRIX_DIR
        target_frame = vision.read_static_image(target_frame_path)
        target_crop_frame = vision.read_static_image(target_crop_frame_path)
        target_matrix = np.load(target_matrix_path)
        target_mask = np.load(target_mask_path)
        swapped_frame = swap(source_embedding, target_frame, target_crop_frame, target_matrix, target_mask)


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


# def apply_enhance(temp_frame, kps: Kps) -> Frame:
#     crop_frame, affine_matrix = enhance_face(temp_frame, kps)
#     crop_mask = mask_face(frame=crop_frame, model_name='face_occluder')
#     paste_frame = paste_back(temp_frame, crop_frame, crop_mask, affine_matrix)
#     face_enhancer_blend = 1 - (80 / 100)
#     return cv2.addWeighted(temp_frame, face_enhancer_blend, paste_frame, 1 - face_enhancer_blend, 0)