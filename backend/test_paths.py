import cv2
import os
from pathlib import Path

DATASET_PATH = Path("../Test dataset")
video_files = [f for f in os.listdir(DATASET_PATH) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]

print(f"Found videos: {video_files}")

for video in video_files:
    video_path = str(DATASET_PATH / video)
    print(f"Testing video path: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        print(f"SUCCESS: {video} opened successfully.")
        ret, frame = cap.read()
        if ret:
            print(f"SUCCESS: Read frame from {video}. Shape: {frame.shape}")
        else:
            print(f"FAILURE: Could not read frame from {video}.")
        cap.release()
    else:
        print(f"FAILURE: Could not open {video}.")
