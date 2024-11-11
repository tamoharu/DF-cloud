from typing import TypedDict, Annotated, Any, Literal, Tuple, Callable, Union, List

import numpy as np
from numpy.typing import NDArray


Frame = Annotated[NDArray[Any], (Any, Any, 3)]
Bbox = Annotated[NDArray[np.float64], (4,)]
BboxList = Annotated[NDArray[np.float64], (Any, 4)] | List[Bbox]
Kp = Annotated[NDArray[np.float64], (2,)]
Kps = Annotated[NDArray[np.float64], (Any, 2)] | List[Kp]
KpsList = Annotated[NDArray[np.float64], (Any, Any, 2)] | List[Kps]
Embedding = np.ndarray[Any, Any]
Output = np.ndarray[Any, Any]
Mask = np.ndarray[Any, Any]
Matrix = np.ndarray[Any, Any]
Angle = float
ResizeData = List[int | float]
Template = np.ndarray[Any, Any]
Size = Tuple[int, int]
UpdateProcess = Callable[[], None]
Resolution = Tuple[int, int]
ProcessFrames = Callable[[List[str], str, UpdateProcess], None]
Process = Literal['swap', 'blur']
DetectFaceModel = Literal['yolov8', 'yolox']
MaskFaceModel = Literal['face_occluder', 'face_parser', 'box']
EnhanceFaceModel = Literal['codeformer']
SwapFaceModel = Literal['inswapper']
MaskFaceRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'eye-glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
TempFrameFormat = Literal['jpg', 'png', 'bmp']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc']
OutputVideoPreset = Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']
ProcessMode = Literal['output', 'preview', 'stream']
LogLevel = Literal['error', 'warn', 'info', 'debug']
VideoMemoryStrategy = Literal['strict', 'moderate', 'tolerant']
Fps = float

class Face(TypedDict):
    kps: Kps

class SystemResources(TypedDict):
    cpu_count: int
    memory_total: float
    memory_available: float
    cpu_usage: float
    memory_usage: float
    io_usage: float