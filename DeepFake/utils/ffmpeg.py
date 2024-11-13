from typing import List
import subprocess

import DeepFake.config.type as type
import DeepFake.utils.log as log
import DeepFake.utils.filesystem as filesystem


def run_ffmpeg(args : List[str]) -> bool:
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
    quality = 2
    commands = ['-hwaccel', 'auto', '-i', video_path, '-q:v', str(quality), '-pix_fmt', 'rgb24', '-vf', f'scale={video_resolution}, fps={video_fps}', '-vsync', '0', frame_pattern]
    return run_ffmpeg(commands)