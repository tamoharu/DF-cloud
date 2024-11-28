from typing import List, Tuple

import numpy as np

import DeepFake.config.type as type
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.inference as inference
import DeepFake.utils.swap_util as swap_util



'''
input
input: [1, 3, 512, 512]
weight: []

output
output: [1, 3, 512, 512]
logits: [1, 256, 1024]
style_feat: [1, 256, 16, 16]
'''


MODEL_PATH = filesystem.resolve_relative_path('')
MODEL_SIZE = (512, 512)
MODEL_TEMPLATE = np.array(
[
    [ 0.37691676, 0.46864664 ],
    [ 0.62285697, 0.46912813 ],
    [ 0.50123859, 0.61331904 ],
    [ 0.39308822, 0.72541100 ],
    [ 0.61150205, 0.72490465 ]
])


def run(crop_frame: type.Frame) -> type.Frame:
    crop_frame = _preprocess(crop_frame)
    output = _forward(crop_frame)
    crop_frame = _postprocess(output)
    return crop_frame


def _forward(crop_frame : type.Frame) -> type.Output:
    session = inference.get_session(MODEL_PATH, 'enhancer')
    input_names = inference.get_input_names(session)
    weight = np.array([ 1 ], dtype = np.double)
    with inference.thread_semaphore():
        output = session.run(None,
        {
            input_names[0]: crop_frame,
            input_names[1]: weight,
        })
    return output



def _preprocess(crop_frame : type.Frame) -> type.Frame:
    crop_frame = crop_frame.astype(np.float32)[:, :, ::-1] / 255.0
    crop_frame = (crop_frame - 0.5) / 0.5
    crop_frame = np.expand_dims(crop_frame.transpose(2, 0, 1), axis = 0).astype(np.float32)
    return crop_frame


def _postprocess(output: type.Output) -> type.Frame:
    crop_frame = output[0][0]
    crop_frame = np.clip(crop_frame, -1, 1)
    crop_frame = (crop_frame + 1) / 2
    crop_frame = crop_frame.transpose(1, 2, 0)
    crop_frame = (crop_frame * 255.0).round()
    crop_frame = crop_frame.astype(np.uint8)[:, :, ::-1]
    return crop_frame