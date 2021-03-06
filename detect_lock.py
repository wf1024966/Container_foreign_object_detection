import numpy as np
import cv2
from IoU import compute_iou
import tools

def bRectToBbox(rect):
    return (rect[1], rect[0], rect[1] + rect[3], rect[0] + rect[2])

def inBbox(pt, bbox):
    if pt[0] >= bbox[1] and pt[0] <= bbox[3] and pt[1] >= bbox[0] and pt[1] <= bbox[2]:
        return True
    else:
        return False

def removeKpRedundancy(bf, desc_background, kp, desc):
    kps_draw = []
    matches = bf.match(desc, desc_background)
    for m in matches:
        kp[m.queryIdx] = None
    for k in kp:
        if k is not None:
            kps_draw.append(k)
    return kps_draw

def removeOutLier(bboxes, kp):
    kp_kept = []
    for bbox in bboxes:
        for pts in kp:
            if inBbox(pts.pt, bbox):
                kp_kept.append(pts)
    return kp_kept

fgbg = cv2.bgsegm.createBackgroundSubtractorGMG()
camera = cv2.VideoCapture('container.mp4')
lock_detector = tools.lock_detector('lock_classifier_2019_3_18_1.pth')

_, firstFrame = camera.read()
for _ in range(10):
    _, firstFrame = camera.read()
ret, frame = camera.read()

count = 0
while ret:
    img = frame.copy()
    fgmask = fgbg.apply(frame)
    th = cv2.threshold(np.copy(fgmask), 244, 255, cv2.THRESH_BINARY)[1]
    th = cv2.erode(th, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=2)
    dilated = cv2.dilate(th, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 3)), iterations=2)
    image, contours, hier = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_kept = []
    bbox_kept = []

    for c in contours:
        if cv2.contourArea(c) > 2000:
            contours_kept.append(c)

    contours_kept.sort(key=lambda x: cv2.contourArea(x), reverse=True)
    if len(contours_kept) >= 1:
        (x, y, w, h) = cv2.boundingRect(contours_kept[0])
        patch = img[(y+h-100):(y+h), (x+w-100):(x+w)]
        result = lock_detector.detect(patch)
        if result == 0:
            cv2.rectangle(img, (x+w-100, y+h-100), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(img, 'lock', (x+w-100, y+h-100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0))
            # cv2.imwrite('./debug_patches/lock_debug_{0:05d}.jpg'.format(count), patch)
            count += 1

    cv2.imshow("detection", img)
    ret, frame = camera.read()  # 读取视频帧数据
    key = cv2.waitKey(10)
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite('output.png', img)

camera.release()
cv2.destroyAllWindows()