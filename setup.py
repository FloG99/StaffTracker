import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt
import cv2
from facenet_pytorch import MTCNN, InceptionResnetV1
from types import MethodType

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.video_width = 640
        self.video_height = 480
        self.video_cam = 0
        self.frame_width = 0
        self.is_centered = False
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.name_label = QLabel(self)
        self.name_label.setText("Name:")
        self.layout.addWidget(self.name_label)

        self.textbox = QLineEdit(self)
        self.textbox.setText("")
        self.layout.addWidget(self.textbox)
        
        self.video_label = QLabel(self)
        self.layout.addWidget(self.video_label)
        
        self.screenshot_button = QPushButton('Bild hinzufügen', self)
        self.screenshot_button.clicked.connect(self.take_screenshot)
        self.layout.addWidget(self.screenshot_button)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update frame every 30 milliseconds
        
        self.mtcnn = MTCNN(image_size=100, keep_all=True, min_face_size=10)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval()
        
        self.detect_face = True
        self.mtcnn.detect_box = MethodType(detect_box, self.mtcnn)  # Replace the detect_box method
        
    def update_frame(self):
        _, frame = self.video_cam.read()
        self.frame_width = frame.shape[1]
        self.frame_height = frame.shape[0]

        if self.detect_face:
            batch_boxes, cropped_images = self.mtcnn.detect_box(frame)
            if cropped_images is not None:
                for box in batch_boxes:
                    x, y, x2, y2 = [int(coord) for coord in box]
                    if self.isPersonCentered(x, x2, y, y2, self.frame_width, self.frame_height):
                        self.is_centered = True
                    else:
                        self.is_centered = False
                    cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0) if self.is_centered else (0, 0, 255), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        qt_pixmap = QPixmap.fromImage(qt_img)
        self.video_label.setPixmap(qt_pixmap.scaled(self.video_width, self.video_height, Qt.KeepAspectRatio))

    def take_screenshot(self):
        name = self.textbox.text()
        if not self.is_centered or len(name) < 2:
            return

        _, frame = self.video_cam.read()
        cv2.imwrite(f"people/{name}.png", frame)
        print("Screenshot taken.")
            

    def isPersonCentered(self, x, x2, y, y2, frame_width, frame_height):
        return (
            x < 0.4 * frame_width and x2 > 0.6 * frame_width and 
            y < 0.25 * frame_height and y2 > 0.75 * frame_height and
            y > 0.1 * frame_height and y2 < 0.9 * frame_height
        )

def detect_box(self, img, save_path=None):
    batch_boxes, batch_probs, batch_points = self.detect(img, landmarks=True)
    if not self.keep_all:
        batch_boxes, batch_probs, batch_points = self.select_boxes(batch_boxes, batch_probs, batch_points, img, method=self.selection_method)
    faces = self.extract(img, batch_boxes, save_path)
    return batch_boxes, faces

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.video_cam = cv2.VideoCapture(main_window.video_cam)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
