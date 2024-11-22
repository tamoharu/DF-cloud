WORDING =\
{
    'box2point/_eye_post': 'invalid eyes',
	'inference/get_session': 'invalid execution providers',
	'swap/merge_video': 'Failed to merge video',
	'swap/restore_audio': 'Failed to restore audio',
}


def get(key: str) -> str:
	return WORDING[key]