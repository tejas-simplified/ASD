import time, os, sys, subprocess
import numpy as np
import cv2
import torch
from torchvision import transforms
from .nets import S3FDNet
from .box_utils import nms_

PATH_WEIGHT = 'model/faceDetector/s3fd/sfd_face.pth'
if os.path.isfile(PATH_WEIGHT) == False:
    Link = "1KafnHz7ccT-3IyddBsL5yi2xGtxAKypt"
    cmd = "gdown --id %s -O %s"%(Link, PATH_WEIGHT)
    subprocess.call(cmd, shell=True, stdout=None)
img_mean = np.array([104., 117., 123.])[:, np.newaxis, np.newaxis].astype('float32')


class S3FD():

    def __init__(self, device='cpu'):

        tstamp = time.time()
        self.device = device

        # print('[S3FD] loading with', self.device)
        self.net = S3FDNet(device=self.device).to(self.device)
        PATH = os.path.join(os.getcwd(), PATH_WEIGHT)
        print("path : ", PATH)
        state_dict = torch.load(PATH, map_location=self.device)
        self.net.load_state_dict(state_dict)
        self.net.eval()
        # print('[S3FD] finished loading (%.4f sec)' % (time.time() - tstamp))
    
    def detect_faces(self, image, conf_th=0.8, scales=[1]):
        print("inside detect faces")

        w, h = image.shape[1], image.shape[0]

        bboxes = np.empty(shape=(0, 5))

        with torch.no_grad():
            for s in scales:
                print("s : ", s)
                scaled_img = cv2.resize(image, dsize=(0, 0), fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
                print("scaled_img : ", scaled_img.shape)
                scaled_img = np.swapaxes(scaled_img, 1, 2)
                print("cp1")
                scaled_img = np.swapaxes(scaled_img, 1, 0)
                print("cp2")
                scaled_img = scaled_img[[2, 1, 0], :, :]
                print("cp3")
                scaled_img = scaled_img.astype('float32')
                print("cp4")
                scaled_img -= img_mean
                print("cp5")
                scaled_img = scaled_img[[2, 1, 0], :, :]
                print("cp6")
                x = torch.from_numpy(scaled_img).unsqueeze(0).to(self.device)
                print("cp7")
                y = self.net(x)
                print("y")

                detections = y.data
                scale = torch.Tensor([w, h, w, h])
                print("new for loop")
                for i in range(detections.size(1)):
                    j = 0
                    while detections[0, i, j, 0] > conf_th:
                        score = detections[0, i, j, 0]
                        # pt = (detections[0, i, j, 1:] * scale).cpu().numpy()
                        pt = (detections[0, i, j, 1:] * scale).numpy()
                        bbox = (pt[0], pt[1], pt[2], pt[3], score)
                        bboxes = np.vstack((bboxes, bbox))
                        j += 1

            keep = nms_(bboxes, 0.1)
            bboxes = bboxes[keep]

        return bboxes
