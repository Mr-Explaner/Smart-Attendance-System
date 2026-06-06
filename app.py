"""
Face Recognition System - PyQt5 Version (ZERO FLICKER GUARANTEED)
==================================================================
Uses PyQt5 for professional-grade, flicker-free video display.
This is the industry standard for live video applications.
"""

import cv2
import numpy as np
import pickle
import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QInputDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
import threading
import time
import datetime
import csv

# Configuration
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "faces.pkl")

# Detection and recognition thresholds (tweak these to reduce false positives/noise)
FACE_SCALE_FACTOR = 1.1
FACE_MIN_NEIGHBORS = 6
FACE_MIN_SIZE = (80, 80)

# Fallback (more sensitive) settings
FACE_SCALE_FACTOR_FALLBACK = 1.05
FACE_MIN_NEIGHBORS_FALLBACK = 4
FACE_MIN_SIZE_FALLBACK = (60, 60)

# Minimum histogram correlation to accept a match (0..1). Increase to reduce false positives.
RECOGNITION_THRESHOLD = 0.75

# Attendance filename prefix
ATTENDANCE_PREFIX = "attendance_"


class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System - Zero Flicker")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton#deleteBtn {
                background-color: #C0392B;
            }
            QPushButton#deleteBtn:hover {
                background-color: #922B21;
            }
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
            QFrame#cameraFrame {
                background-color: #000000;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Error", "Could not open camera!")
            sys.exit(1)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Load face cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load face database
        self.faces_db = self.load_faces()
        
        # Current frame
        self.current_frame = None
        self.running = True
        
        # Setup UI
        self.setup_ui()
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        
        # Setup timer for updating display (FLICKER-FREE!)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 33 FPS
    
    def setup_ui(self):
        """Create the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left side - Camera feed
        left_layout = QVBoxLayout()
        
        # Camera title
        camera_title = QLabel("📹 Live Camera Feed")
        camera_title.setFont(QFont("Arial", 18, QFont.Bold))
        camera_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(camera_title)
        
        # Camera display (QLabel for video - FLICKER-FREE!)
        camera_frame = QFrame()
        camera_frame.setObjectName("cameraFrame")
        camera_frame_layout = QVBoxLayout()
        camera_frame.setLayout(camera_frame_layout)
        
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(780, 585)
        self.camera_label.setScaledContents(True)
        self.camera_label.setAlignment(Qt.AlignCenter)
        camera_frame_layout.addWidget(self.camera_label)
        
        left_layout.addWidget(camera_frame)
        
        # Right side - Controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        
        # Title
        title = QLabel("Face Recognition\nControl Panel")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("System Ready")
        self.status_label.setFont(QFont("Arial", 13))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: lightgreen;")
        right_layout.addWidget(self.status_label)
        
        # Register button
        register_btn = QPushButton("➕ Register New Face")
        register_btn.setFixedHeight(50)
        register_btn.clicked.connect(self.register_face)
        right_layout.addWidget(register_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete Face")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.setFixedHeight(50)
        delete_btn.clicked.connect(self.delete_face)
        right_layout.addWidget(delete_btn)
        
        # Registered faces label
        faces_label = QLabel("Registered Faces:")
        faces_label.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(faces_label)
        
        # Faces list
        self.faces_textbox = QTextEdit()
        self.faces_textbox.setReadOnly(True)
        right_layout.addWidget(self.faces_textbox)

        # Attendance section
        attendance_label = QLabel("Today's Attendance:")
        attendance_label.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(attendance_label)

        self.attendance_textbox = QTextEdit()
        self.attendance_textbox.setReadOnly(True)
        self.attendance_textbox.setFixedHeight(180)
        right_layout.addWidget(self.attendance_textbox)

        # Attendance buttons
        attendance_btn_layout = QHBoxLayout()
        export_btn = QPushButton("⬇️ Export CSV")
        export_btn.setFixedHeight(40)
        export_btn.clicked.connect(self.export_attendance)
        attendance_btn_layout.addWidget(export_btn)

        reset_btn = QPushButton("♻️ Reset")
        reset_btn.setFixedHeight(40)
        reset_btn.clicked.connect(self.reset_attendance)
        attendance_btn_layout.addWidget(reset_btn)

        right_layout.addLayout(attendance_btn_layout)
        
        # Add layouts to main
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(820)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setFixedWidth(350)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # Update faces list
        self.update_faces_list()
        # Load today's attendance and update UI
        self.attendance = self.load_attendance()
        self.update_attendance_list()

    
    def camera_loop(self):
        """Background thread for reading camera frames"""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.current_frame = frame
            time.sleep(0.001)
    
    def update_frame(self):
        """Update the camera display - TRULY FLICKER-FREE with PyQt5!"""
        if self.current_frame is not None:
            frame = self.current_frame.copy()
            
            # Detect and annotate faces
            frame = self.detect_and_annotate(frame)
            
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize to display size
            frame_resized = cv2.resize(frame_rgb, (780, 585))
            
            # Convert to QImage (PyQt5's native format - ZERO FLICKER!)
            h, w, ch = frame_resized.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_resized.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Update QLabel with QPixmap (HARDWARE ACCELERATED - NO FLICKER!)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))
    
    def detect_and_annotate(self, frame):
        """Detect faces and draw annotations"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=FACE_SCALE_FACTOR, minNeighbors=FACE_MIN_NEIGHBORS, minSize=FACE_MIN_SIZE
        )
        
        if len(faces) == 0:
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=FACE_SCALE_FACTOR_FALLBACK, minNeighbors=FACE_MIN_NEIGHBORS_FALLBACK, minSize=FACE_MIN_SIZE_FALLBACK
            )
        
        # Annotate each face
        for (x, y, w, h) in faces:
            face_region = frame[y:y+h, x:x+w]
            name, confidence = self.recognize_face(face_region)
            
            if name == "Unknown":
                color = (0, 100, 255)
                label = "Unknown Person"
            else:
                color = (0, 255, 0)
                label = f"{name} ({confidence:.0%})"
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
            
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            label_y = max(y - 10, label_size[1] + 10)
            cv2.rectangle(frame, (x, label_y - label_size[1] - 10),
                         (x + label_size[0] + 10, label_y + 5), color, -1)
            cv2.putText(frame, label, (x + 5, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            # If recognized, try to mark attendance (only once per day)
            if name != "Unknown":
                newly_marked = False
                try:
                    newly_marked = self.mark_attendance(name)
                except Exception:
                    newly_marked = False
                if newly_marked:
                    # Fetch info if available
                    saved = self.faces_db.get(name, {})
                    info = saved.get('info', {}) if isinstance(saved, dict) else {}
                    id_text = info.get('id', '')
                    details = f"Name: {name}\n"
                    if id_text:
                        details += f"ID: {id_text}\n"
                    details += f"Marked at: {self.attendance.get(name)}"
                    QMessageBox.information(self, "Marked Present", details)
        
        instruction = f"Faces Detected: {len(faces)}"
        cv2.putText(frame, instruction, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        return frame
    
    def encode_face(self, face_img):
        """Create face encoding using histogram"""
        face_img = cv2.resize(face_img, (128, 128))
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    # ---------------- Attendance helpers ----------------
    def _attendance_filepath(self):
        today = datetime.date.today().isoformat()
        return os.path.join(DATA_DIR, f"{ATTENDANCE_PREFIX}{today}.pkl")

    def load_attendance(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        path = self._attendance_filepath()
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}

    def save_attendance(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        path = self._attendance_filepath()
        with open(path, 'wb') as f:
            pickle.dump(self.attendance, f)

    def mark_attendance(self, name):
        # Mark only once per day
        if name in self.attendance:
            return False
        timestamp = datetime.datetime.now().isoformat(timespec='seconds')
        self.attendance[name] = timestamp
        self.save_attendance()
        self.update_attendance_list()
        return True

    def update_attendance_list(self):
        if not hasattr(self, 'attendance') or len(self.attendance) == 0:
            self.attendance_textbox.setText("No one marked present yet.")
            return
        lines = [f"{i}. {name} - {ts}" for i, (name, ts) in enumerate(sorted(self.attendance.items()), 1)]
        self.attendance_textbox.setText("\n".join(lines))

    def export_attendance(self):
        if not hasattr(self, 'attendance') or len(self.attendance) == 0:
            QMessageBox.information(self, "No Attendance", "No attendance to export.")
            return
        today = datetime.date.today().isoformat()
        csv_path = os.path.join(DATA_DIR, f"attendance_{today}.csv")
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Name', 'Timestamp'])
                for name, ts in sorted(self.attendance.items()):
                    writer.writerow([name, ts])
            QMessageBox.information(self, "Exported", f"Attendance exported to {csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def reset_attendance(self):
        reply = QMessageBox.question(self, "Reset Attendance",
                                     "Clear today's attendance?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.attendance = {}
            self.save_attendance()
            self.update_attendance_list()
            QMessageBox.information(self, "Reset", "Today's attendance cleared.")

    
    def recognize_face(self, face_img):
        """Recognize a face by comparing with database"""
        if len(self.faces_db) == 0:
            return "Unknown", 0.0
        
        face_encoding = self.encode_face(face_img)
        best_match = "Unknown"
        best_score = 0.0
        for name, saved in self.faces_db.items():
            # saved may be either raw encoding (old format) or dict with 'encoding'
            saved_encoding = saved['encoding'] if isinstance(saved, dict) and 'encoding' in saved else saved
            score = cv2.compareHist(
                face_encoding.astype(np.float32),
                saved_encoding.astype(np.float32),
                cv2.HISTCMP_CORREL
            )
            if score > best_score:
                best_score = score
                best_match = name
        
        if best_score < RECOGNITION_THRESHOLD:
            return "Unknown", best_score
        
        return best_match, best_score
    
    def register_face(self):
        """Register a new face"""
        if self.current_frame is None:
            QMessageBox.critical(self, "Error", "No camera feed available!")
            return
        
        name, ok = QInputDialog.getText(self, "Register New Face", 
                                        "Enter the person's name:")
        
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        if name in self.faces_db:
            reply = QMessageBox.question(self, "Name Exists",
                                        f"'{name}' is already registered. Update it?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        frame = self.current_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=FACE_SCALE_FACTOR, minNeighbors=FACE_MIN_NEIGHBORS, minSize=FACE_MIN_SIZE
        )
        
        if len(faces) == 0:
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=FACE_SCALE_FACTOR_FALLBACK, minNeighbors=FACE_MIN_NEIGHBORS_FALLBACK, minSize=FACE_MIN_SIZE_FALLBACK
            )
        
        if len(faces) == 0:
            QMessageBox.critical(self, "No Face Detected",
                               "No face detected!\n\n"
                               "• Look directly at camera\n"
                               "• Ensure good lighting\n"
                               "• Move closer\n"
                               "• Remove face coverings")
            self.set_status("Registration failed - No face detected", "red")
            return
        
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_region = frame[y:y+h, x:x+w]
        
        try:
            face_encoding = self.encode_face(face_region)
            # Ask for optional ID or notes
            id_text, ok_id = QInputDialog.getText(self, "Person ID (optional)",
                                                  "Enter an ID or notes for this person (optional):")
            info = {'id': id_text.strip()} if ok_id and id_text.strip() else {}
            # Store new format
            self.faces_db[name] = {'encoding': face_encoding, 'info': info}
            self.save_faces()
            self.update_faces_list()
            QMessageBox.information(self, "Success", 
                                   f"'{name}' registered successfully!")
            self.set_status(f"✅ Registered: {name}", "lightgreen")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to register:\n{str(e)}")
            self.set_status("Registration failed", "red")
    
    def delete_face(self):
        """Delete a registered face"""
        if len(self.faces_db) == 0:
            QMessageBox.information(self, "No Faces", "No registered faces!")
            return
        
        names = sorted(self.faces_db.keys())
        name, ok = QInputDialog.getItem(self, "Delete Face",
                                        "Select face to delete:", names, 0, False)
        
        if not ok:
            return
        
        reply = QMessageBox.question(self, "Confirm Deletion",
                                    f"Delete '{name}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            del self.faces_db[name]
            self.save_faces()
            self.update_faces_list()
            QMessageBox.information(self, "Success", f"'{name}' deleted!")
            self.set_status(f"🗑️ Deleted: {name}", "orange")
    
    def load_faces(self):
        """Load face database"""
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'rb') as f:
                    data = pickle.load(f)
                    # Migrate older format where value was raw encoding array
                    migrated = {}
                    for name, val in data.items():
                        if isinstance(val, dict) and 'encoding' in val:
                            migrated[name] = val
                        else:
                            migrated[name] = {'encoding': val, 'info': {}}
                    return migrated
            except:
                return {}
        return {}
    
    def save_faces(self):
        """Save face database"""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(self.faces_db, f)
    
    def update_faces_list(self):
        """Update the list of registered faces"""
        if len(self.faces_db) == 0:
            self.faces_textbox.setText("No faces registered yet.\n\n"
                                      "Click 'Register New Face' to add someone!")
        else:
            text = "📋 Registered People:\n\n"
            for i, name in enumerate(sorted(self.faces_db.keys()), 1):
                text += f"{i}. {name}\n"
            text += f"\nTotal: {len(self.faces_db)} face(s)"
            self.faces_textbox.setText(text)
    
    def set_status(self, message, color="lightgreen"):
        """Update status message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
    
    def closeEvent(self, event):
        """Handle window closing"""
        self.running = False
        if self.cap is not None:
            self.cap.release()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
