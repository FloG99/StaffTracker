from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import torch
import os
import cv2
from tqdm import tqdm
from types import MethodType
import gui

def encode(img):
    res = resnet(torch.Tensor(img))
    return res

def detect_box(self, img, save_path=None):
    batch_boxes, batch_probs, batch_points = self.detect(img, landmarks=True)
    if not self.keep_all:
        batch_boxes, batch_probs, batch_points = self.select_boxes(batch_boxes, batch_probs, batch_points, img, method=self.selection_method)
    faces = self.extract(img, batch_boxes, save_path)
    return batch_boxes, faces

def detect_motion(frame1, frame2, threshold=0.3):
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    frame_diff = cv2.absdiff(gray1, gray2)
    motion_area_percentage = (frame_diff > 10).mean()
    return motion_area_percentage > threshold

def isPersonCentered(x, x2, frameWidth):
    return (
        x < 0.5 * frameWidth and x2 > 0.5 * frameWidth
    )


# Load model
resnet = InceptionResnetV1(pretrained='vggface2').eval()
mtcnn = MTCNN(image_size=100, keep_all=True, min_face_size=10)
mtcnn.detect_box = MethodType(detect_box, mtcnn)

# Load people
src_path,_ = os.path.split(os.path.realpath(__file__))
input_dir = os.path.join(src_path, "people")
all_people_faces = {}
for file in os.listdir(input_dir):
    person = file.split(".")[0]
    img = cv2.imread(f'{input_dir}/{file}')
    cropped = mtcnn(img)
    if cropped is not None:
        print("Loaded " + person)
        all_people_faces[person] = encode(cropped)[0, :]

def detect(cam=0):
    vdo = cv2.VideoCapture(cam)
    thres = 0.75
    frameWidth = vdo.get(cv2.CAP_PROP_FRAME_WIDTH)
    motion_detected_cooldown = 0
    frame_drop_interval = 5
    frame_count = 0
    _, prev_frame = vdo.read()

    print("Scanner active")

    while vdo.grab():
        _, curr_frame = vdo.read()
        frame_count += 1
        motion_detected_cooldown -= 1

        if motion_detected_cooldown < 0 and frame_count % frame_drop_interval != 0:
            continue

        if motion_detected_cooldown < 0 and not detect_motion(prev_frame, curr_frame):
            continue
        prev_frame = curr_frame

        batch_boxes, cropped_images = mtcnn.detect_box(curr_frame)
        if cropped_images is not None:
            for box, cropped in zip(batch_boxes, cropped_images):
                x, y, x2, y2 = [int(x) for x in box]


                # cv2.rectangle(curr_frame, (x, y), (x2, y2), (0, 0, 255), 2)
                # cv2.putText(curr_frame, "x", (x + 5, y + 10), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
                # cv2.imshow("output", curr_frame)
                # if cv2.waitKey(1) == ord('q'):
                #     cv2.destroyAllWindows()

                if not isPersonCentered(x, x2, frameWidth):
                    continue

                # Centered person detected. Now don't skip any frames for while, for maximum accuracy
                motion_detected_cooldown = 100

                img_embedding = encode(cropped.unsqueeze(0))
                detect_dict = {}
                for k, v in all_people_faces.items():
                    detect_dict[k] = (v - img_embedding).norm().item()
                min_key = min(detect_dict, key=detect_dict.get)

                if detect_dict[min_key] < thres:
                    return min_key

if __name__ == "__main__":
    while True:
        person = detect(0)
        print(person + " detected!")
        gui.open(person)
