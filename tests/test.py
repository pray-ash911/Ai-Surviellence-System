import tensorflow as tf
import tensorflow_hub as hub
import cv2

# Load MoViNet model (streaming)
print("Loading MoViNet model...")
model = hub.load("https://tfhub.dev/tensorflow/movinet/a0/stream/kinetics-600/classification/3")

# Load labels
with open("labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

print("Total labels loaded:", len(labels))

# Violence-related keywords
violent_actions = ["punch", "kick", "fight", "wrestl", "attack", "shoot", "stab", "assault"]

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Preprocess frame
    img = cv2.resize(frame, (172, 172)) / 255.0
    input_tensor = tf.expand_dims(img, 0)

    # Prediction
    outputs = model(input_tensor)
    pred_class = tf.argmax(outputs, axis=1).numpy()[0]
    pred_label = labels[pred_class]

    # Violence detection logic
    if any(v in pred_label.lower() for v in violent_actions):
        status = "⚠️ Violence Detected"
        color = (0, 0, 255)  # red
    else:
        status = "✅ Non-violent"
        color = (0, 255, 0)  # green

    # Overlay results
    cv2.putText(frame, f"Action: {pred_label}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, status, (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

    # Show video
    cv2.imshow("MoViNet Violence Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
