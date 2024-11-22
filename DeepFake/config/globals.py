import DeepFake.config.type as type

PJ_NAME: str = 'df_inference'
FRAME_DIR: str = '/frames'
CROP_FRAME_DIR: str = '/crop_frames'
MASK_DIR: str = '/masks'
MATRIX_DIR: str = '/matrices'
SOURCE_EMBEDDING_DIR: str = '/embedding'
SWAPPED_FRAME_DIR: str = '/swapped'
TEMP_DIR: str = '/temp'
FRAME_EXTENSION: str = '.jpg'
VIDEO_EXTENSION: str = '.mp4'
MASK_EXTENSION: str = '.npy'
MATRIX_EXTENSION: str = '.npy'
EMBEDDING_EXTENSION: str = '.npy'


VIDEO_FPS: int = 30
VIDEO_QUALITY: int = 70
VIDEO_ENCODER: type.OutputVideoEncoder = 'libx264'
VIDEO_PRESET: type.OutputVideoPreset = 'veryfast'