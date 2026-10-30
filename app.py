import io
import os
import subprocess
import sys

import face_recognition
import numpy as np
import streamlit as st
from PIL import Image, ImageOps

from dashboard import render_header, show_dashboard

st.set_page_config(page_title="Face Attendance System", page_icon="📋", layout="wide")

render_header()

# ---------- Sidebar: short project explanation ----------
with st.sidebar:
    st.header("About this project")
    st.write("Marks attendance automatically by recognising each student's face.")

    st.subheader("How it works")
    st.markdown(
        "1. **Detect** the face in the camera frame\n"
        "2. **Encode** it as 128 numbers\n"
        "3. **Match** it with registered students\n"
        "4. **Blink check** to confirm a real person\n"
        "5. **Save** name, date and time in a CSV file"
    )

    st.subheader("Built with")
    st.markdown("- Python\n- OpenCV\n- face_recognition (dlib)\n- pandas\n- Streamlit")

tab_attendance, tab_register, tab_dashboard = st.tabs(
    ["Take Attendance", "Register Student", "Dashboard"]
)

# ---------- Tab 1: Take attendance ----------
with tab_attendance:
    st.subheader("Take attendance")

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 1. Start")
            st.write("Click the button below. A camera window will open.")
    with c2:
        with st.container(border=True):
            st.markdown("### 2. Blink")
            st.write("Look at the camera and blink once. Attendance is marked automatically.")
    with c3:
        with st.container(border=True):
            st.markdown("### 3. Close")
            st.write("Press **q** on the camera window to close it.")

    st.write("")
    if st.button("Start attendance camera", type="primary"):
        subprocess.Popen(
            [sys.executable, "attendance_live.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        st.success("The camera window is opening. Press q on that window to close it.")

# ---------- Tab 2: Register a new student ----------
with tab_register:
    st.subheader("Register a new student")
    st.write(
        "Enter the name and add a clear photo: face straight to the camera, "
        "good light, only one person in the photo."
    )

    name = st.text_input("Student name (do not end the name with a number)")
    method = st.radio(
        "How do you want to add the photo?",
        ["Upload a photo", "Take photo with camera"],
        horizontal=True,
    )

    photo = None
    if method == "Upload a photo":
        photo = st.file_uploader("Choose a photo (JPG or PNG)", type=["jpg", "jpeg", "png"])
    else:
        st.info("Close the attendance camera window before using this camera.")
        photo = st.camera_input("Take photo")

    if photo is not None and name.strip() != "":
        if st.button("Save student", type="primary"):
            pil = ImageOps.exif_transpose(Image.open(io.BytesIO(photo.getvalue())))
            pil = pil.convert("RGB")
            pil.thumbnail((1000, 1000))
            found = face_recognition.face_encodings(np.array(pil))

            if len(found) == 0:
                st.error("No face found in the photo. Please use another photo.")
            elif len(found) > 1:
                st.error("More than one face found. Please keep only one person in the photo.")
            else:
                os.makedirs("known_faces", exist_ok=True)
                clean = name.strip()
                path = "known_faces/" + clean + ".jpg"
                n = 2
                while os.path.exists(path):
                    path = "known_faces/" + clean + str(n) + ".jpg"
                    n = n + 1
                pil.save(path, "JPEG")
                st.success("Saved: " + path + ". Restart the attendance camera to load the new student.")

# ---------- Tab 3: Dashboard ----------
with tab_dashboard:
    show_dashboard()