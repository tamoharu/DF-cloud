from typing import Optional
from threading import Lock

import onnxruntime

import DeepFake.config.type as type


_MODEL_TYPES = tuple(type.ModelType.__args__)


_instances: dict[str, Optional[onnxruntime.InferenceSession]] = {
    model_type: None for model_type in _MODEL_TYPES
}


_locks: dict[str, Lock] = {
    model_type: Lock() for model_type in _MODEL_TYPES
}


def get_instance(model_type: type.ModelType) -> Optional[onnxruntime.InferenceSession]:
    global _instances
    return _instances.get(model_type)


def set_instance(model_type: type.ModelType, session: onnxruntime.InferenceSession) -> None:
    global _instances
    _instances[model_type] = session