import numpy as np
import onnx

import DeepFake.config.type as type
import DeepFake.utils.filesystem as filesystem
import DeepFake.utils.inference as inference


'''
input
target: [1, 3, 128, 128]
source: [1, 512]

output
output: [1, 3, 128, 128]
'''


MODEL_PATH = filesystem.resolve_relative_path('../../models/inswapper.onnx')
MODEL_SIZE = (128, 128)
MODEL_TEMPLATE = np.array(
[
    [ 0.36167656, 0.40387734 ],
    [ 0.63696719, 0.40235469 ],
    [ 0.50019687, 0.56044219 ],
    [ 0.38710391, 0.72160547 ],
    [ 0.61507734, 0.72034453 ]
])


def run(target_crop_frame: type.Frame, source_embedding: type.Embedding) -> type.Frame:
    source_embedding = _prepare_source(source_embedding)
    target_frame = _prepare_target(target_crop_frame)
    output = _forward(target_frame, source_embedding)
    crop_frame = _postprocess(output)
    return crop_frame


def _forward(target_frame: type.Frame, source_embedding: type.Embedding) -> type.Output:
    session = inference.get_session(MODEL_PATH)
    input_names = inference.get_input_names(session)
    with inference.thread_semaphore():
        output = session.run(None,
        {
            input_names[0]: target_frame,
            input_names[1]: source_embedding,
        })
    return output


def _postprocess(output: type.Output) -> type.Frame:
    crop_frame = output[0][0]
    crop_frame = (crop_frame.astype(np.float32) * 255.0).round()
    crop_frame = crop_frame.transpose(1, 2, 0)
    crop_frame = crop_frame[:, :, ::-1]
    return crop_frame


def _prepare_source(embedding: type.Embedding) -> type.Embedding:
    embedding = embedding.reshape((1, -1))
    model_matrix = get_model_matrix(onnx.load(MODEL_PATH))
    embedding = np.dot(embedding, model_matrix) / np.linalg.norm(embedding)
    return embedding


def _prepare_target(crop_frame: type.Frame) -> type.Frame:
    crop_frame = crop_frame[:, :, ::-1] / np.array([255.0])
    crop_frame = (crop_frame) / [1.0, 1.0, 1.0]
    crop_frame = crop_frame.transpose(2, 0, 1)
    crop_frame = np.expand_dims(crop_frame, axis = 0).astype(np.float32)
    return crop_frame


def get_model_matrix(model: onnx.ModelProto) -> type.Matrix:
    model_matrix = onnx.numpy_helper.to_array(model.graph.initializer[-1])
    return model_matrix