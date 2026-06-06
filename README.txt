Face Recognition Authentication System

A desktop-based Face Recognition Authentication System developed using Python and PyQt5. The application provides real-time face detection and recognition through a webcam, allowing users to register their faces and authenticate themselves securely. The project features a modern user interface, smooth video rendering, and local face data storage.

---

Introduction

Traditional password-based authentication systems can be inconvenient and vulnerable to password theft. This project introduces a biometric authentication solution that uses facial recognition technology to identify and verify users.

The system captures live video from a camera, detects faces in real time, compares them with registered face data, and grants access only to recognized users. The application is designed with a professional PyQt5 interface to ensure a smooth and flicker-free user experience.

---

Objectives

- Detect faces from a live camera feed.
- Register new users using facial data.
- Recognize and authenticate registered users.
- Display recognition confidence levels.
- Provide a user-friendly desktop application.
- Store face data locally without requiring an external database.

---

Features

- Real-time face detection.
- Face registration and enrollment.
- Face recognition and authentication.
- Modern PyQt5 graphical user interface.
- Smooth video display with zero flickering.
- Confidence percentage display.
- Local file-based storage.
- Cross-platform compatibility.

---

Technologies Used

Programming Language

- Python

Libraries and Frameworks

- PyQt5
- OpenCV
- NumPy
- Pickle

Development Tools

- VS Code / PyCharm
- Python Virtual Environment

---

System Architecture

Input Layer

- Webcam captures real-time video frames.

Processing Layer

- Face detection identifies faces from incoming frames.
- Feature extraction generates facial features.
- Recognition engine compares detected faces with registered face data.

Storage Layer

- Registered face information is stored locally in a Pickle file.

Output Layer

- Displays recognized user names and confidence scores.
- Grants or denies access based on recognition results.

---

Project Structure

FaceRecognitionSystem/
│
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── faces.pkl
│
├── assets/
│   ├── icons/
│   └── images/
│
└── models/

---

Working Principle

Step 1: Face Registration

1. User clicks the Register button.
2. Camera captures the user's face.
3. User enters a name.
4. Face features are extracted and stored.

Step 2: Face Recognition

1. Camera continuously captures frames.
2. Face detection identifies faces in the frame.
3. Extracted features are compared with stored face data.
4. If a match is found:
   - User name is displayed.
   - Access is granted.
5. If no match is found:
   - Face is marked as Unknown.
   - Access is denied.

---

Installation

Clone Repository

git clone https://github.com/yourusername/FaceRecognitionSystem.git
cd FaceRecognitionSystem

Install Dependencies

pip install -r requirements.txt

Run Application

python app.py

---

Requirements

- Python 3.8+
- Webcam
- Windows, Linux, or macOS

---

Future Enhancements

- Deep Learning based recognition using FaceNet or DeepFace.
- Multiple user management.
- Attendance management system.
- Face unlock for desktop applications.
- Cloud database integration.
- Anti-spoofing protection against photos and videos.
- User activity logs.

---

Applications

- Secure login systems.
- Attendance management.
- Office access control.
- Smart home authentication.
- Educational projects and research.

---

Conclusion

The Face Recognition Authentication System demonstrates the practical use of computer vision and biometric authentication. It provides a secure and user-friendly alternative to traditional password-based systems while showcasing the capabilities of real-time face detection and recognition using Python and PyQt5.

---

Author

Adnan Ali

Bachelor of Science in Data Science

Educational Project
