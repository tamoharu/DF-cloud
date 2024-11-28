import os
import DeepFake.core.mask as mask


def run():
  # local_paths = os.listdir(local_dir)
  # for local_path in local_paths:
  #   local_path = local_dir + '/' + local_path
  #   output_dir = os.path.basename(local_path).split()[-1] + '/output'
  #   mask.run(local_path, output_dir)
  local_path = './videos/6037743_Person_People_3840x2160 - (9 x 16)_1.mp4'
  output_dir = os.path.basename(local_path).split()[-1] + '/output'
  mask.run(local_path, output_dir)


if __name__ == '__main__':
  run()