# import cv2
# import numpy as np
# import dlib
# from scipy.spatial import distance
import threading
import queue
from datetime import datetime, timedelta


# class FatigueDetector:
#     def __init__(self, config):
#         self.config = config
#         self.detector = dlib.get_frontal_face_detector()
#         self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
#         self.camera_lock = threading.Lock()
#         self.frame_queue = queue.Queue(maxsize=30)
#         self.camera_in_use = False
#         self.current_camera_app = None

#     def calculate_ear(self, eye):
#         # Calculate the eye aspect ratio
#         A = distance.euclidean(eye[1], eye[5])
#         B = distance.euclidean(eye[2], eye[4])
#         C = distance.euclidean(eye[0], eye[3])
#         ear = (A + B) / (2.0 * C)
#         return ear

#     def detect_blink(self, frame):
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = self.detector(gray)

#         for face in faces:
#             landmarks = self.predictor(gray, face)
#             left_eye = []
#             right_eye = []

#             # Extract eye coordinates
#             for n in range(36, 42):
#                 left_eye.append((landmarks.part(n).x, landmarks.part(n).y))
#             for n in range(42, 48):
#                 right_eye.append((landmarks.part(n).x, landmarks.part(n).y))

#             left_ear = self.calculate_ear(left_eye)
#             right_ear = self.calculate_ear(right_eye)
#             avg_ear = (left_ear + right_ear) / 2

#             return avg_ear < self.config.settings['detection_settings']['blink_threshold']

#         return False

#     def detect_yawn(self, frame):
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = self.detector(gray)

#         for face in faces:
#             landmarks = self.predictor(gray, face)
#             mouth_points = []

#             # Extract mouth coordinates
#             for n in range(48, 68):
#                 mouth_points.append((landmarks.part(n).x, landmarks.part(n).y))

#             top_lip = mouth_points[13:16]
#             bottom_lip = mouth_points[17:20]

#             top_mean = np.mean(top_lip, axis=0)
#             bottom_mean = np.mean(bottom_lip, axis=0)

#             mouth_open = abs(top_mean[1] - bottom_mean[1])
#             face_height = abs(landmarks.part(8).y - landmarks.part(27).y)

#             ratio = mouth_open / face_height
#             return ratio > self.config.settings['detection_settings']['yawn_threshold']

#         return False
    


import mediapipe as mp
import cv2
import numpy as np
from scipy.spatial import distance

class FatigueDetector:
    def __init__(self, config):
        self.config = config
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.camera_lock = threading.Lock()
        self.frame_queue = queue.Queue(maxsize=30)
        self.camera_in_use = False
        self.current_camera_app = None

    def calculate_ear(self, frame):
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return 1.0  # Return normal EAR when no face detected
            
        face_landmarks = results.multi_face_landmarks[0]
        
        # Eye landmarks indices for MediaPipe Face Mesh
        LEFT_EYE = [362, 385, 387, 263, 373, 380]
        RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
        # Get coordinates for both eyes
        left_eye_points = np.array([[face_landmarks.landmark[i].x * frame.shape[1],
                                   face_landmarks.landmark[i].y * frame.shape[0]] 
                                  for i in LEFT_EYE])
        right_eye_points = np.array([[face_landmarks.landmark[i].x * frame.shape[1],
                                    face_landmarks.landmark[i].y * frame.shape[0]] 
                                   for i in RIGHT_EYE])
        
        # Calculate EAR for both eyes
        left_ear = self._calculate_ear_points(left_eye_points)
        right_ear = self._calculate_ear_points(right_eye_points)
        
        return (left_ear + right_ear) / 2.0
        
    def _calculate_ear_points(self, eye_points):
        # Calculate the vertical distances
        A = distance.euclidean(eye_points[1], eye_points[5])
        B = distance.euclidean(eye_points[2], eye_points[4])
        # Calculate the horizontal distance
        C = distance.euclidean(eye_points[0], eye_points[3])
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
        
    def detect_yawn(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return False
            
        face_landmarks = results.multi_face_landmarks[0]
        
        # Mouth landmarks indices
        UPPER_LIPS = [13, 14, 312]
        LOWER_LIPS = [17, 18, 314]
        
        # Get coordinates for lips
        upper_lip_points = np.array([[face_landmarks.landmark[i].y * frame.shape[0]
                                    for i in UPPER_LIPS]])
        lower_lip_points = np.array([[face_landmarks.landmark[i].y * frame.shape[0]
                                    for i in LOWER_LIPS]])
        
        # Calculate mouth opening
        mouth_opening = np.mean(lower_lip_points) - np.mean(upper_lip_points)
        
        # Get face height for normalization
        face_top = min([face_landmarks.landmark[i].y for i in range(len(face_landmarks.landmark))])
        face_bottom = max([face_landmarks.landmark[i].y for i in range(len(face_landmarks.landmark))])
        face_height = (face_bottom - face_top) * frame.shape[0]
        
        # Calculate ratio
        mouth_ratio = mouth_opening / face_height
        
        return mouth_ratio > self.config.settings['detection_settings']['yawn_threshold']

    def detect_blink(self, frame):
        ear = self.calculate_ear(frame)
        return ear < self.config.settings['detection_settings']['blink_threshold']