from typing import List
import subprocess
import os

import DeepFake.config.type as type
import DeepFake.config.globals as globals
import DeepFake.utils.log as log
import DeepFake.utils.filesystem as filesystem


def run_ffmpeg(args: List[str]) -> bool:
	commands = [ 'ffmpeg', '-hide_banner', '-loglevel', 'error' ]
	commands.extend(args)
	try:
		subprocess.run(commands, stderr = subprocess.PIPE, check = True)
		return True
	except subprocess.CalledProcessError as exception:
		log.debug(exception.stderr.decode().strip(), __name__.upper())
		return False


def extract_frames(video_path: str, video_resolution: str, video_fps: type.Fps) -> bool:
    frame_pattern = filesystem.get_temp_frames_pattern(video_path, '%5d')
    commands = ['-hwaccel', 'auto', '-i', video_path, '-q:v', '2', '-pix_fmt', 'rgb24', '-vf', f'scale={video_resolution}, fps={video_fps}', '-vsync', '0', frame_pattern]
    return run_ffmpeg(commands)


def merge_video(frames_dir: str, output_path: str, video_fps: type.Fps) -> bool:
	frames_pattern = os.path.join(frames_dir, '%5d' + globals.FRAME_EXTENSION)
	commands = [ '-hwaccel', 'auto', '-r', str(video_fps), '-i', frames_pattern, '-c:v', globals.VIDEO_ENCODER ]
	if globals.VIDEO_ENCODER in [ 'libx264', 'libx265' ]:
		output_video_compression = round(51 - (globals.VIDEO_QUALITY * 0.51))
		commands.extend([ '-crf', str(output_video_compression), '-preset', globals.VIDEO_PRESET ])
	if globals.VIDEO_ENCODER in [ 'libvpx-vp9' ]:
		output_video_compression = round(63 - (globals.VIDEO_QUALITY * 0.63))
		commands.extend([ '-crf', str(output_video_compression) ])
	if globals.VIDEO_ENCODER in [ 'h264_nvenc', 'hevc_nvenc' ]:
		output_video_compression = round(51 - (globals.VIDEO_QUALITY * 0.51))
		commands.extend([ '-cq', str(output_video_compression), '-preset', map_nvenc_preset(globals.VIDEO_PRESET) ])
	commands.extend([ '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-y', output_path ])
	return run_ffmpeg(commands)


def restore_audio(original_video_path: str, temp_output_path: str, output_path: str) -> bool:
    commands = ['-hwaccel', 'auto', '-i', temp_output_path]
    commands.extend(['-i', original_video_path, '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path])
    return run_ffmpeg(commands)


def map_nvenc_preset(VIDEO_PRESET: type.OutputVideoPreset) -> str:
	if VIDEO_PRESET in [ 'ultrafast', 'superfast', 'veryfast' ]:
		return 'p1'
	if VIDEO_PRESET == 'faster':
		return 'p2'
	if VIDEO_PRESET == 'fast':
		return 'p3'
	if VIDEO_PRESET == 'medium':
		return 'p4'
	if VIDEO_PRESET == 'slow':
		return 'p5'
	if VIDEO_PRESET == 'slower':
		return 'p6'
	if VIDEO_PRESET == 'veryslow':
		return 'p7'
	else:
		raise