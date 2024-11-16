import cv2
import numpy as np
import dlib
from scipy.spatial import distance
import threading
import queue
from datetime import datetime, timedelta


class FatigueDetector:
    def __init__(self, config):
        self.config = config
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        self.camera_lock = threading.Lock()
        self.frame_queue = queue.Queue(maxsize=30)
        self.camera_in_use = False
        self.current_camera_app = None

    def calculate_ear(self, eye):
        # Calculate the eye aspect ratio
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        C = distance.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def detect_blink(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        for face in faces:
            landmarks = self.predictor(gray, face)
            left_eye = []
            right_eye = []

            # Extract eye coordinates
            for n in range(36, 42):
                left_eye.append((landmarks.part(n).x, landmarks.part(n).y))
            for n in range(42, 48):
                right_eye.append((landmarks.part(n).x, landmarks.part(n).y))

            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            avg_ear = (left_ear + right_ear) / 2

            return avg_ear < self.config.settings['detection_settings']['blink_threshold']

        return False

    def detect_yawn(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        for face in faces:
            landmarks = self.predictor(gray, face)
            mouth_points = []

            # Extract mouth coordinates
            for n in range(48, 68):
                mouth_points.append((landmarks.part(n).x, landmarks.part(n).y))

            top_lip = mouth_points[13:16]
            bottom_lip = mouth_points[17:20]

            top_mean = np.mean(top_lip, axis=0)
            bottom_mean = np.mean(bottom_lip, axis=0)

            mouth_open = abs(top_mean[1] - bottom_mean[1])
            face_height = abs(landmarks.part(8).y - landmarks.part(27).y)

            ratio = mouth_open / face_height
            return ratio > self.config.settings['detection_settings']['yawn_threshold']

        return False