import cv2
import numpy as np
import os
from pathlib import Path

def generate_video(filename, width=640, height=480, fps=15, duration=30, obj_color=(200, 200, 200), defect_color=(0,0,255), speed=8):
    out_path = Path("../Test dataset") / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
    
    total_frames = fps * duration
    
    # Colors
    bg_color = (100, 100, 100)
    belt_color = (60, 60, 60)
    
    obj_w, obj_h = 120, 120
    
    objects = []
    
    for frame_idx in range(total_frames):
        frame = np.ones((height, width, 3), dtype=np.uint8) * np.array(bg_color, dtype=np.uint8)
        
        # Draw belt
        belt_x1 = width // 2 - 150
        belt_x2 = width // 2 + 150
        cv2.rectangle(frame, (belt_x1, 0), (belt_x2, height), belt_color, -1)
        
        # Draw moving lines on belt for parallax
        line_spacing = 40
        offset = (frame_idx * speed) % line_spacing
        for y in range(-line_spacing, height, line_spacing):
            cv2.line(frame, (belt_x1, y + offset), (belt_x2, y + offset), (40, 40, 40), 5)
            
        # Spawn new object (every roughly 2 seconds)
        if frame_idx % (fps * 2) == 0:
            is_defective = np.random.rand() < 0.25 # 25% defect rate
            x_pos = belt_x1 + (belt_x2 - belt_x1)//2 - obj_w//2
            objects.append({"y": -obj_h, "is_defective": is_defective, "x": x_pos})
            
        # Update and draw objects
        for obj in objects:
            obj["y"] += speed
            x = obj["x"]
            y = int(obj["y"])
            
            if y < height:
                # Draw the base item
                cv2.rectangle(frame, (x, y), (x + obj_w, y + obj_h), obj_color, -1)
                cv2.rectangle(frame, (x, y), (x + obj_w, y + obj_h), (20,20,20), 3)
                
                # Inner details
                cv2.circle(frame, (x + obj_w//2, y + obj_h//2), 20, (50,50,50), -1)
                
                # If defective, draw something that the YOLO model was trained on
                if obj["is_defective"]:
                    # Draw a distinct blue line/crack or scratch 
                    # (This is similar to what the train_yolo script generated for "defective")
                    cv2.line(frame, (x + 20, y + 20), (x + 80, y + 80), (255, 0, 0), 6)
                    cv2.circle(frame, (x + 30, y + 70), 10, (0, 0, 255), -1)
                    
        # Remove offscreen objects
        objects = [o for o in objects if o["y"] < height]
        
        out.write(frame)
        
    out.release()
    print(f"Generated {out_path} ({duration}s, {fps}fps)")

if __name__ == '__main__':
    print("Generating synthetic conveyor videos for Test dataset...")
    generate_video("conveyor_03.mp4", obj_color=(180, 200, 180), speed=6)
    generate_video("conveyor_04.mp4", obj_color=(200, 180, 180), speed=10)
    print("Generation complete!")
