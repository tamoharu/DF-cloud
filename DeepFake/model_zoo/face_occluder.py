import cv2
import numpy as np

import config.type as type
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.inference as inference


'''
input
in_face:0: ['unk__359', 256, 256, 3]

output
out_mask:0: ['unk__360', 256, 256, 1]
'''


MODEL_SIZE = (256, 256)
MODEL_PATH = filesystem.resolve_relative_path('../../models/face_occluder.onnx')


def run(frame: type.Frame) -> type.Mask:
    prepare_frame = _preprocess(frame)
    output = _forward(prepare_frame)
    mask = _postprocess(output, frame)
    return mask


def _preprocess(frame: type.Frame) -> type.Frame:
    frame = cv2.resize(frame, MODEL_SIZE, interpolation = cv2.INTER_LINEAR)
    frame = np.expand_dims(frame, axis = 0).astype(np.float32) / 255
    return frame


def _forward(frame: type.Frame) -> type.Output:
    session = inference.get_session(MODEL_PATH)
    input_names = inference.get_input_names(session)
    with inference.thread_semaphore():
        output = session.run(None,
        {
            input_names[0]: frame,
        })
    return output


def _postprocess(output: type.Output, frame: type.Frame) -> type.Mask:
    mask = output[0][0]
    occlusion_mask = mask.transpose(0, 1, 2).clip(0, 1).astype(np.float32)
    occlusion_mask = cv2.resize(occlusion_mask, frame.shape[:2][::-1])
    return occlusion_mask