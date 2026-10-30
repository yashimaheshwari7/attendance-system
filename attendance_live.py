import os
import csv
import cv2
import face_recognition
from math import dist
from datetime import datetime

EAR_LIMIT = 0.21
MIN_CLOSED = 1
SCALE = 0.5

def eye_ratio(eye):
    a = dist(eye[1], eye[5])
    b = dist(eye[2], eye[4])
    c = dist(eye[0], eye[3])
    return (a + b) / (2.0 * c)

# 1. Saved chehre load karo
known_encodings = []
known_names = []

for file in os.listdir("known_faces"):
    image = face_recognition.load_image_file("known_faces/" + file)
    found = face_recognition.face_encodings(image)
    if len(found) == 0:
        print(file, "mein chehra nahi mila, skip")
        continue
    known_encodings.append(found[0])
    known_names.append(file.split(".")[0].rstrip("0123456789"))

if len(known_encodings) == 0:
    print("known_faces mein koi chehra nahi mila")
    exit()

print("Taiyar hoon. Palak jhapkao tab attendance lagegi.")

# 2. CSV taiyar karo
if not os.path.exists("attendance.csv"):
    with open("attendance.csv", "w", newline="") as f:
        csv.writer(f).writerow(["Name", "Date", "Time"])

today = datetime.now().strftime("%d-%m-%Y")
marked = set()

with open("attendance.csv", "r") as f:
    for row in csv.reader(f):
        if len(row) == 3 and row[1] == today:
            marked.add(row[0])

def mark_attendance(name):
    if name in marked:
        return
    marked.add(name)
    now = datetime.now()
    with open("attendance.csv", "a", newline="") as f:
        csv.writer(f).writerow(
            [name, now.strftime("%d-%m-%Y"), now.strftime("%H:%M:%S")]
        )
    print("Attendance lag gayi:", name)

# 3. Webcam chalao
closed = {}
cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cam.read()
    if not ret:
        break

    small = cv2.resize(frame, (0, 0), fx=SCALE, fy=SCALE)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations)
    landmarks = face_recognition.face_landmarks(rgb, locations)

    for enc, loc, lm in zip(encodings, locations, landmarks):
        distances = face_recognition.face_distance(known_encodings, enc)
        best = distances.argmin()

        name = "Unknown"
        color = (0, 0, 255)
        status = ""

        if distances[best] < 0.5:
            name = known_names[best]
            color = (0, 255, 0)

            if name not in marked:
                ear = (eye_ratio(lm["left_eye"]) + eye_ratio(lm["right_eye"])) / 2
                if ear < EAR_LIMIT:
                    closed[name] = closed.get(name, 0) + 1
                else:
                    if closed.get(name, 0) >= MIN_CLOSED:
                        mark_attendance(name)
                    closed[name] = 0

            if name in marked:
                status = "Present"
            else:
                status = "Palak jhapkao"

        top, right, bottom, left = [int(v / SCALE) for v in loc]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name + " " + status, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Attendance", frame)
    if cv2.waitKey(1) == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()