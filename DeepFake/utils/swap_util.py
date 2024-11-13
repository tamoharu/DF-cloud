from typing import Tuple, List

import cv2
import numpy as np

import DeepFake.config.type as type
import DeepFake.core.model_zoo.yolox as detector
import DeepFake.core.model_zoo.inswapper as swapper


def warp_face(temp_frame: type.Frame, kps: type.Kps, model_template: type.Template, model_size: type.Size) -> Tuple[type.Frame, type.Matrix]:
    normed_template = model_template * model_size
    filtered_kps = np.array([row for row in kps if row is not None and not np.isnan(row).any()])
    filtered_template = np.array([row for row, reference_row in zip(normed_template, kps) if reference_row is not None and not np.isnan(reference_row).any()])
    affine_matrix = cv2.estimateAffinePartial2D(filtered_kps, filtered_template, method=cv2.RANSAC, ransacReprojThreshold=100)[0]
    crop_frame = cv2.warpAffine(temp_frame, affine_matrix, model_size, borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_AREA)
    return crop_frame, affine_matrix


def crop_frame(frame: type.Frame) -> Tuple[List[type.Frame], List[type.Matrix]]:
    model_size = swapper.MODEL_SIZE
    model_template = swapper.MODEL_TEMPLATE
    normed_template = model_template * model_size
    kps_list = detector.run(frame)
    if len(kps_list) == 0:
        return [], []
    crop_frame_list = []
    affine_matrix_list = []
    for kps in kps_list:
        filtered_kps = np.array([row for row in kps if row is not None and not np.isnan(row).any()])
        filtered_template = np.array([row for row, reference_row in zip(normed_template, kps) if reference_row is not None and not np.isnan(reference_row).any()])
        if len(filtered_kps) < 2:
            continue
        affine_matrix = cv2.estimateAffinePartial2D(filtered_kps, filtered_template, method=cv2.RANSAC, ransacReprojThreshold=100)[0]
        crop_frame = cv2.warpAffine(frame, affine_matrix, model_size, borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_AREA)
        crop_frame_list.append(crop_frame)
        affine_matrix_list.append(affine_matrix)
    return crop_frame_list, affine_matrix_list