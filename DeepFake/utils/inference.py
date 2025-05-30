import platform
import subprocess
import threading
from typing import List

import onnxruntime

import DeepFake.config.instance as instance
import DeepFake.config.device as device
import DeepFake.config.type as type
import DeepFake.config.words as words
import DeepFake.utils.log as log


onnxruntime.set_default_logger_severity(3)


def thread_lock() -> threading.Lock:
    return threading.Lock()


def thread_semaphore() -> threading.Semaphore:
    return threading.Semaphore()


def _has_nvidia_gpu() -> bool:
    system = platform.system().lower()
    try:
        if system == "windows":
            process = subprocess.Popen(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return process.wait() == 0
        elif system == "linux":
            process = subprocess.Popen(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "nvidia" in process.communicate()[0].decode().lower()
        return False
    except FileNotFoundError:
        return False


def _has_amd_gpu() -> bool:
    system = platform.system().lower()
    try:
        if system == "windows":
            process = subprocess.Popen(['dxdiag'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return any(gpu in process.communicate()[0].decode().lower() for gpu in ["amd", "radeon"])
        elif system == "linux":
            process = subprocess.Popen(['lspci'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return any(gpu in process.communicate()[0].decode().lower() for gpu in ["amd", "radeon"])
        return False
    except FileNotFoundError:
        return False


def get_execution_providers() -> List[str]:
    _providers = device.execution_providers
    if _providers:
        return _providers
    with thread_lock():
        _providers = device.execution_providers
        if _providers:
            return _providers
        available_providers = onnxruntime.get_available_providers()
        providers = []
        if 'CUDAExecutionProvider' in available_providers and _has_nvidia_gpu():
            providers.append('CUDAExecutionProvider')
        if 'DMLExecutionProvider' in available_providers and (_has_nvidia_gpu() or _has_amd_gpu()):
            providers.append('DMLExecutionProvider')
        if 'CoreMLExecutionProvider' in available_providers and platform.system().lower() == 'darwin':
            providers.append('CoreMLExecutionProvider')
        if 'ROCMExecutionProvider' in available_providers and _has_amd_gpu():
            providers.append('ROCMExecutionProvider')
        providers.append('CPUExecutionProvider')
        device.execution_providers = providers
        return providers


def get_session(model_path: str, model_type: type.ModelType) -> onnxruntime.InferenceSession:
    session = instance.get_instance(model_type)
    if session:
        return session
    with instance._locks[model_type]:
        session = instance.get_instance(model_type)
        if session:
            return session
        execution_providers = get_execution_providers()
        try:
            session = onnxruntime.InferenceSession(str(model_path), providers=execution_providers)
        except:
            log.error(words.get('inference/get_session'), __name__.upper())
            session = onnxruntime.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
        instance.set_instance(model_type, session)
        return session

def get_input_names(session: onnxruntime.InferenceSession) -> List[str]:
    return [input.name for input in session.get_inputs()]


def get_output_names(session: onnxruntime.InferenceSession) -> List[str]:
    return [output.name for output in session.get_outputs()]


def get_input_shape(session: onnxruntime.InferenceSession) -> List[List[int]]:
    return [input.shape for input in session.get_inputs()]


def get_output_shape(session: onnxruntime.InferenceSession) -> List[List[int]]:
    return [output.shape for output in session.get_outputs()]