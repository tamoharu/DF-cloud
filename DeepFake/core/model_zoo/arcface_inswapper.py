import numpy as np

import DeepFake.config.type as type
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.inference as inference


'''
input
input.1: ['None', 3, 112, 112]

output
683: [1, 512]
'''


MODEL_SIZE = (112, 112)
MODEL_TEMPLATE = np.array(
[
    [ 0.36167656, 0.40387734 ],
    [ 0.63696719, 0.40235469 ],
    [ 0.50019687, 0.56044219 ],
    [ 0.38710391, 0.72160547 ],
    [ 0.61507734, 0.72034453 ]
])
MODEL_PATH = filesystem.resolve_relative_path('../../models/face_recognizer.onnx')
    

def run(frame: type.Frame) -> type.Embedding:
    crop_frame = _preprocess(frame)
    output = _forward(crop_frame)
    embedding = _postprocess(output)
    return embedding


def _preprocess(crop_frame: type.Frame) -> type.Frame:
    crop_frame = crop_frame.astype(np.float32) / 127.5 - 1
    crop_frame = crop_frame[:, :, ::-1].transpose(2, 0, 1)
    crop_frame = np.expand_dims(crop_frame, axis = 0)
    return crop_frame


def _forward(frame: type.Frame) -> type.Output:
    session = inference.get_session(MODEL_PATH)
    input_names = inference.get_input_names(session)
    with inference.thread_semaphore():
        output = session.run(None,
        {
            input_names[0]: frame,
        })
    return output


def _postprocess(output: type.Output) -> type.Embedding:
    return output[0].ravel()