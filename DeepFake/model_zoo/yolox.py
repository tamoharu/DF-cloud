# input: image[1, 3, H, W]
# output: kps[5, 2]
# kps: [left_eye, right_eye, nose, left_mouth, right_mouth]

from typing import List, Tuple

import cv2
import numpy as np

import config.type as type
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.inference as inference
import DeepFake.utils.box2point as box2point


'''
input
input: [1, 3, 640, 640]

output
batchno_classid_score_x1y1x2y2: ['N', 7]
'''


MODEL_SIZE = (640, 640)
MODEL_PATH = filesystem.resolve_relative_path('../../models/yolox.onnx')


def run(frame: type.Frame) -> type.KpsList:
    frame, resize_data = _preprocess(frame)
    output = _forward(frame)
    results = _postprocess(output, resize_data)
    return results


def _preprocess(frame: type.Frame) -> Tuple[type.Frame, type.ResizeData]:
    frame_height, frame_width = frame.shape[:2]
    resize_ratio = min(MODEL_SIZE[0] / frame_height, MODEL_SIZE[1] / frame_width)
    resized_shape = int(round(frame_width * resize_ratio)), int(round(frame_height * resize_ratio))
    frame = cv2.resize(frame, resized_shape, interpolation=cv2.INTER_LINEAR)
    offset_height = round((MODEL_SIZE[0] - resized_shape[1]) / 2 - 0.1)
    offset_width = round((MODEL_SIZE[1] - resized_shape[0]) / 2 - 0.1)
    resize_data = [offset_height, offset_width, resize_ratio]
    frame = cv2.copyMakeBorder(frame, offset_height, offset_height, offset_width, offset_width, cv2.BORDER_CONSTANT, value = (114, 114, 114))
    frame = frame.transpose(2, 0, 1)
    frame = frame.astype(np.float32)
    frame = np.expand_dims(frame, axis = 0)
    frame = np.ascontiguousarray(frame)
    return frame, resize_data


def _forward(frame: type.Frame) -> type.Output:
    session = inference.get_session(MODEL_PATH)
    input_names = inference.get_input_names(session)
    with inference.thread_semaphore():
        output = session.run(None,
        {
            input_names[0]: frame
        })
    return output


def _postprocess(detections: type.Output, resize_data: type.ResizeData) -> type.KpsList:
    offset_height, offset_width, resize_ratio = resize_data[0], resize_data[1], resize_data[2]
    detections = np.array(detections)
    detections[:, :, 3::2] = (detections[:, :, 3::2] - offset_width) / resize_ratio
    detections[:, :, 4::2] = (detections[:, :, 4::2] - offset_height) / resize_ratio
    face_boxes = detections[detections[:, :, 1] == 3]
    if len(face_boxes) == 0:
        return []
    eye_boxes = detections[detections[:, :, 1] == 4]
    nose_boxes = detections[detections[:, :, 1] == 5]
    mouth_boxes = detections[detections[:, :, 1] == 6]
    face_boxes = face_boxes[:, 3:]
    eye_boxes = eye_boxes[:, 3:]
    nose_boxes = nose_boxes[:, 3:]
    mouth_boxes = mouth_boxes[:, 3:]
    results = box2point.run(face_boxes, eye_boxes, nose_boxes, mouth_boxes)
    return results