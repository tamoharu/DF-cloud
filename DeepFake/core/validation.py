import numpy as np
import DeepFake.core.model_zoo.yolox as detector


def validation(frame):
    kps_list = detector.run(frame)
    validate_kps_list = []
    for kps in kps_list:
        filtered_kps = np.array([row for row in kps if row is not None and not np.isnan(row).any()])
        if len(filtered_kps) < 2:
            continue
        validate_kps_list.append(kps)
    if len(validate_kps_list) != 1:
        return False
    return True