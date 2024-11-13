from typing import Tuple

import numpy as np

import DeepFake.config.type as type
import DeepFake.config.words as words
import DeepFake.utils.log as log


'''
input
face_boxes: [N, 4]
eye_boxes: [N, 4]
nose_boxes: [N, 4]
mouth_boxes: [N, 4]

type.Output
kps: [N, 5, 2]
'''


def run(face_boxes: type.BboxList, eye_boxes: type.BboxList, nose_boxes: type.BboxList, mouth_boxes: type.BboxList) -> type.KpsList:
    results = []
    if len(face_boxes) == 0:
        return results
    # len(face_boxes) >= 1
    for face_box in face_boxes:
        eye_left_point, eye_right_point, nose_point, mouth_left_point, mouth_right_point = None, None, None, None, None
        # 0 <= len(eye_boxes) <= 2
        eye_boxes_filtered = _filter_boxes(eye_boxes, face_box, max_items=2)
        # 0 <= len(nose_boxes) <= 1
        nose_boxes_filtered = _filter_boxes(nose_boxes, face_box, max_items=1)
        # 0 <= len(mouth_boxes) <= 1
        mouth_boxes_filtered = _filter_boxes(mouth_boxes, face_box, max_items=1)
        # bottom to top, vertical angle
        face_angle = _calc_face_angle(face_box, eye_boxes_filtered, nose_boxes_filtered, mouth_boxes_filtered)
        nose_point = _nose_post(nose_boxes_filtered, face_angle)
        mouth_left_point, mouth_right_point = _mouth_post(mouth_boxes_filtered, face_angle)
        eye_left_point, eye_right_point = _eye_post(face_box, eye_boxes_filtered, nose_boxes_filtered , mouth_boxes_filtered, face_angle)
        kps = np.zeros((5, 2))
        kps[0] = eye_left_point
        kps[1] = eye_right_point
        kps[2] = nose_point
        kps[3] = mouth_left_point
        kps[4] = mouth_right_point
        results.append(kps)
    return results


def _filter_boxes(boxes: type.BboxList, face_box: type.Bbox, max_items: int) -> type.BboxList:
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = face_box[0], face_box[1], face_box[2], face_box[3]
    inface_boxes = []
    for box in boxes:
        box_cx = (box[0] + box[2]) / 2
        box_cy = (box[1] + box[3]) / 2
        if x1 <= box_cx <= x2 and y1 <= box_cy <= y2:
            inface_boxes.append(box)
    if len(inface_boxes) > max_items:
        distances = []
        face_cx = (x1 + x2) / 2
        face_cy = (y1 + y2) / 2
        for box in inface_boxes:
            box_cx = (box[0] + box[2]) / 2
            box_cy = (box[1] + box[3]) / 2
            distance = (box_cx - face_cx) ** 2 + (box_cy - face_cy) ** 2
            distances.append((distance, box))
        distances.sort(key=lambda x: x[0]) 
        filtered_boxes = [box for _, box in distances[:max_items]]
    else:
        filtered_boxes = inface_boxes
    return filtered_boxes


def _calc_face_angle(face_box: type.Bbox, eye_boxes: type.BboxList, nose_boxes: type.BboxList, mouth_boxes: type.BboxList) -> type.Angle:
    eyes_center = None
    nose_center = None
    mouth_center = None
    if len(eye_boxes) == 2:
        eye_1_center =  [(eye_boxes[0][0] + eye_boxes[0][2]) / 2, (eye_boxes[0][1] + eye_boxes[0][3]) / 2]
        eye_2_center =  [(eye_boxes[1][0] + eye_boxes[1][2]) / 2, (eye_boxes[1][1] + eye_boxes[1][3]) / 2]
        eyes_center = [(eye_1_center[0] + eye_2_center[0]) / 2, (eye_1_center[1] + eye_2_center[1]) / 2]
    if len(nose_boxes) == 1:
        nose_box = nose_boxes[0]
        nose_center = [(nose_box[0] + nose_box[2]) / 2, (nose_box[1] + nose_box[3]) / 2]
    if len(mouth_boxes) == 1:
        mouth_box = mouth_boxes[0]
        mouth_center = [(mouth_box[0] + mouth_box[2]) / 2, (mouth_box[1] + mouth_box[3]) / 2]
    if eyes_center is not None:
        if nose_center is not None:
            dx = eyes_center[0] - nose_center[0]
            dy = eyes_center[1] - nose_center[1]
            return np.arctan2(dy, dx)
        if mouth_center is not None:
            dx = eyes_center[0] - mouth_center[0]
            dy = eyes_center[1] - mouth_center[1]
            return np.arctan2(dy, dx)
        dx = eyes_center[0] - face_box[0]
        dy = eyes_center[1] - face_box[1]
        return np.arctan2(dy, dx)
    if mouth_center is not None:
        if nose_center is not None:
            dx = nose_center[0] - mouth_center[0]
            dy = nose_center[1] - mouth_center[1]
            return np.arctan2(dy, dx)
        dx = face_box[0] - mouth_center[0]
        dy = face_box[1] - mouth_center[1]
        return np.arctan2(dy, dx)
    return np.pi / 2


def _eye_post(face_box: type.Bbox, eye_boxes: type.BboxList, nose_boxes_filtered: type.BboxList, mouth_boxes_filtered: type.BboxList, face_angle: float) -> Tuple[type.Kp | None, type.Kp | None]:
    if len(eye_boxes) == 0:
        return None, None
    eyes_centers = []
    for eye in eye_boxes:
        eye_center = [(eye[0] + eye[2]) / 2, (eye[1] + eye[3]) / 2]
        eyes_centers.append(eye_center)
    face_center = [(face_box[0] + face_box[2]) / 2, (face_box[1] + face_box[3]) / 2]
    if len(eye_boxes) == 1:
        eye_center = eyes_centers[0]
        if len(nose_boxes_filtered) == 1:
            dx = eye_center[0] - nose_boxes_filtered[0][0]
            dy = eye_center[1] - nose_boxes_filtered[0][1]
        elif len(mouth_boxes_filtered) == 1:
            dx = eye_center[0] - mouth_boxes_filtered[0][0]
            dy = eye_center[1] - mouth_boxes_filtered[0][1]
        else:
            dx = eye_center[0] - face_center[0]
            dy = eye_center[1] - face_center[1]
        eye_angle = np.arctan2(dy, dx)
        if eye_angle > face_angle:
            left_eye_point = eye_center
            right_eye_point = None
        else:
            left_eye_point = None
            right_eye_point = eye_center
        return left_eye_point, right_eye_point
    if len(eye_boxes) == 2:
        angles = []
        for eye_center in eyes_centers:
            if len(mouth_boxes_filtered) == 1:
                dx = eye_center[0] - mouth_boxes_filtered[0][0]
                dy = eye_center[1] - mouth_boxes_filtered[0][1]
            elif len(nose_boxes_filtered) == 1:
                dx = eye_center[0] - nose_boxes_filtered[0][0]
                dy = eye_center[1] - nose_boxes_filtered[0][1]
            else:
                dx = eye_center[0] - face_center[0]
                dy = eye_center[1] - face_center[1]
            angle = np.arctan2(dy, dx)
            angles.append(angle)
        if angles[0] < angles[1]:
            left_eye_point, right_eye_point = eyes_centers
        else:
            left_eye_point, right_eye_point = eyes_centers[::-1]
        return left_eye_point, right_eye_point
    log.error(words.get('box2point/eye_post'), __name__.upper())
    raise
    

def _nose_post(nose_boxes: type.BboxList, face_angle: type.Angle) -> type.Kp | None:
    if len(nose_boxes) == 0:
        return None
    coef = 0.25
    nose_box = nose_boxes[0]
    dx = np.cos(face_angle) * (nose_box[2] - nose_box[0]) / 2
    dy = np.sin(face_angle) * (nose_box[3] - nose_box[1]) / 2
    nose_center = [(nose_box[0] + nose_box[2]) / 2, (nose_box[1] + nose_box[3]) / 2]
    nose_point = np.array([nose_center[0] - dx * coef, nose_center[1] - dy * coef])
    return nose_point


def _mouth_post(mouth_boxes: type.BboxList, face_angle: type.Angle) -> Tuple[type.Kp | None, type.Kp | None]:
    if len(mouth_boxes) == 0:
        return None, None
    mouth_box = mouth_boxes[0]
    h_angle = face_angle - np.pi / 2
    mouth_center = [(mouth_box[0] + mouth_box[2]) / 2, (mouth_box[1] + mouth_box[3]) / 2]
    dx = np.cos(h_angle) * (mouth_box[2] - mouth_box[0]) / 2
    dy = np.sin(h_angle) * (mouth_box[3] - mouth_box[1]) / 2
    mouth_left_point = np.array([mouth_center[0] - dx, mouth_center[1] - dy])
    mouth_right_point = np.array([mouth_center[0] + dx, mouth_center[1] + dy])
    if h_angle < -np.pi / 2 or h_angle > np.pi / 2:
        mouth_left_point, mouth_right_point = mouth_right_point, mouth_left_point
    return mouth_left_point, mouth_right_point