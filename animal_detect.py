from ultralytics import YOLO
import cv2
import serial
import time
from pushbullet import Pushbullet
import os
from datetime import datetime

# Load YOLOv9 model
model = YOLO('yolov9c.pt')

# COCO dataset class IDs
class_map = {
    0: "human",
    20: "elephant",
    22: "zebra",
    21: "bear",
    24: "giraffe"
}

# Set of class IDs we want to detect
target_classes = list(class_map.keys())

# Open camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Connect to Arduino
try:
    arduino = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)
    arduino_connected = True
except Exception as e:
    print(f"Failed to connect to Arduino: {e}")
    arduino_connected = False

# Pushbullet tokens
pushbullet_tokens = [
    "o.QOqMmNCqV3tZiHWfT43AIi4YHsTIelWk",
    "o.ryw7V7lcQKje7KgVR5RyXTUfCaw7XGyM"
]

# Initialize Pushbullet clients
pb_clients = []
for token in pushbullet_tokens:
    try:
        pb_clients.append(Pushbullet(token))
        print(f"Pushbullet initialized: {token[:10]}...")
    except Exception as e:
        print(f"Failed to initialize Pushbullet for {token[:10]}...: {e}")

pushbullet_connected = len(pb_clients) > 0

# States
led_on = False
last_alert_time = 0
alert_cooldown = 5 # seconds

# Function to send Pushbullet alert with image
def send_alert(detected_animals, frame):
    global last_alert_time
    current_time = time.time()

    if current_time - last_alert_time > alert_cooldown:
        if pushbullet_connected and detected_animals:
            title = "Wild Animal Alert!"

            # Construct message from detected animal counts
            message_parts = []
            for animal, count in detected_animals.items():
                label = animal if count == 1 else animal + "s"
                message_parts.append(f"{count} {label}")

            message = ", ".join(message_parts) + " detected! Be alert and stay safe!"

            # Save frame to file
            alert_folder = "alerts"
            os.makedirs(alert_folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"alert_{timestamp}.jpg"
            image_path = os.path.join(alert_folder, image_filename)
            cv2.imwrite(image_path, frame)

            # Send message and image to all Pushbullet clients
            for pb in pb_clients:
                try:
                    pb.push_note(title, message)
                    print(f"Alert sent: {message}")
                    with open(image_path, "rb") as pic:
                        pb.push_file(pic, file_name=image_filename, file_type="image/jpeg", body=message)
                        print(f"Image {image_filename} sent via Pushbullet.")
                except Exception as e:
                    print(f"Failed to send alert/image with token {pb.api_key[:10]}...: {e}")

            last_alert_time = current_time
        else:
            print(f"Would send alert: {detected_animals}")
    else:
        print("Alert cooldown active.")

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Run YOLOv9 detection
    results = model(frame, classes=target_classes)

    # Count detected animals
    detected_animals = {
        "elephant": 0,
        "bear": 0,
        "giraffe": 0,
        "zebra": 0,
        "human": 0
    }

    for box in results[0].boxes:
        class_id = int(box.cls)
        if class_id in class_map:
            label = class_map[class_id]
            detected_animals[label] += 1

    # Show detected humans but don't alert
    if detected_animals["human"] > 0:
        print(f"Human(s) detected: {detected_animals['human']} (No alert)")

    # Determine if any animal (excluding human) is detected
    should_alert = any(detected_animals[animal] > 0 for animal in ["elephant", "bear", "giraffe", "zebra"])

    # Annotate frame
    annotated_frame = results[0].plot()

    # Handle alert + LED logic
    if should_alert:
        if not led_on and arduino_connected:
            arduino.write(b'H')  # Turn on buzzer/LED
            led_on = True
            print("Animal detected! LED ON.")
        send_alert({k: v for k, v in detected_animals.items() if k != "human" and v > 0}, annotated_frame)
    else:
        if led_on and arduino_connected:
            arduino.write(b'L')  # Turn off buzzer/LED
            led_on = False
            print("No animals detected. LED OFF.")

    # Display result
    cv2.imshow("Real-Time Animal Detection", annotated_frame)

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
if arduino_connected:
    arduino.close()
