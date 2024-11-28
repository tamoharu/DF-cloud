import DeepFake.core.swap as swap


if __name__ == '__main__':
    local_source_dir = './sources/trump'
    local_target_dir = './targets/7022012_20s_Adult_3840x2160_1_1.mp4/output'
    local_output_dir = './outputs'
    original_video_path = './videos/7022012_20s_Adult_3840x2160_1_1.mp4'
    swap.run(local_source_dir, local_target_dir, local_output_dir, original_video_path)