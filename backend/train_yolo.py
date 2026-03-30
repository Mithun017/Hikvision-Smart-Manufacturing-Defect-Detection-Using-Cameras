import cv2
import numpy as np
import os
from pathlib import Path
from ultralytics import YOLO
import random
import yaml

def create_yolo_dataset(video_path, output_dir, num_frames=50):
    dataset_path = Path(output_dir)
    for subtype in ['train', 'val']:
        (dataset_path / subtype / 'images').mkdir(parents=True, exist_ok=True)
        (dataset_path / subtype / 'labels').mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Sampling {num_frames} frames from {video_path}...")

    frame_indices = sorted(random.sample(range(total_frames), min(num_frames, total_frames)))
    
    frame_count = 0
    while cap.isOpened() and frame_count < num_frames:
        ret, frame = cap.read()
        if not ret: break
        
        idx = frame_indices[frame_count]
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret: break

        subtype = 'train' if random.random() < 0.8 else 'val'
        img_name = f"frame_{frame_count:04d}.jpg"
        img_path = dataset_path / subtype / 'images' / img_name
        label_path = dataset_path / subtype / 'labels' / f"frame_{frame_count:04d}.txt"

        # Simple object detection for labeling (Contour detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        labels = []
        h, w, _ = frame.shape
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 500 < area < 100000: # Filter small noise
                x, y, bw, bh = cv2.boundingRect(cnt)
                
                # Normalize for YOLO format (class_id, x_center, y_center, width, height)
                xc, yc = (x + bw/2)/w, (y + bh/2)/h
                n_bw, n_bh = bw/w, bh/h
                
                # Class 0: Clean, Class 1: Defective
                # Randomly assign 15% to "Defective" and simulate it in the image
                class_id = 0
                if random.random() < 0.15:
                    class_id = 1
                    # Draw a synthetic "crack" (blue line) for the model to learn
                    cv2.line(frame, (x + bw//4, y + bh//4), (x + 3*bw//4, y + 3*bh//4), (255, 0, 0), 3)
                
                labels.append(f"{class_id} {xc} {yc} {n_bw} {n_bh}")

        if labels:
            cv2.imwrite(str(img_path), frame)
            with open(label_path, 'w') as f:
                f.write("\n".join(labels))
            frame_count += 1

    cap.release()
    print("Dataset generation complete.")

def main():
    root_dir = Path(".")
    video_source = root_dir / "../Test dataset/conveyor_01.mp4"
    dataset_dir = root_dir / "industrial_dataset"
    
    if not video_source.exists():
        print(f"ERROR: Video not found at {video_source}")
        return

    create_yolo_dataset(video_source, dataset_dir)

    # Create dataset.yaml
    yaml_content = {
        'path': str(dataset_dir.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'names': {0: 'clean', 1: 'defective'}
    }
    
    with open(root_dir / 'dataset.yaml', 'w') as f:
        yaml.dump(yaml_content, f)

    print("Starting YOLOv8n training...")
    model = YOLO('yolov8n.pt') 
    model.train(data=str(root_dir / 'dataset.yaml'), epochs=10, imgsz=640, batch=4)
    
    # Save the final model
    print("Training complete. Exporting model to industrial_vision.pt...")
    model.export(format='pt')
    # Copy the best weight to root for backend use
    best_model = Path("runs/detect/train/weights/best.pt")
    if best_model.exists():
        import shutil
        shutil.copy(best_model, root_dir / "industrial_vision.pt")
        print("Success: Model saved as industrial_vision.pt")

if __name__ == "__main__":
    main()
