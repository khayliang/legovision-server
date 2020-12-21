import cv2
import numpy as np
from enum import Enum
from shapely.geometry import Polygon

class LegoSize(Enum):
    TWO = (0, 90)
    THREE = (90, 110)
    FOUR = (110, 150)
    SIX = (150, 180)
    EIGHT = (180, 10000)

class LegoColor(Enum):
    GREY = (0, 15, 1)
    LIGHT_GREY = (15, 33, 1)
    LIME = (23,38, 0)
    GREEN = (38,71, 0)
    BLUE = (108, 126, 0)
    ORANGE = (0,10, 0)
    YELLOW = (12,25,0)
    AZURE = (98, 108, 0)

class LegoDetector:
    def __init__(self):
        pass
    
    def preprocess(self, img):
        edges = cv2.Canny(img,50,150)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        dilated = cv2.dilate(edges, kernel)
        return dilated
        
    def generate_contours(self, img):
        cnts, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return cnts
    
    def generate_rects(self, contours):
        rects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 1000:
                continue

            # approximate the contour
            rect = cv2.minAreaRect(c)

            size = rect[1]
            if size[0]<50  or size[1]<50:
                continue

            rects.append(rect)
        return rects

    def rects_pipeline(self, img):
        processed = self.preprocess(img)
        contours = self.generate_contours(processed)
        rects = self.generate_rects(contours)
        return rects

    def remove_duplicate_rects(self, rects_1, rects_2):
        kinda_final = rects_1
        iou_thresh = 0.1
        polygons_1 = [Polygon(box) for box in self.rects_to_boxes(rects_1)]
        polygons_2 = [Polygon(box) for box in self.rects_to_boxes(rects_2)]
        final_polygons = polygons_1

        for idx, b in enumerate(polygons_2):
            within = False
            for a in polygons_1:
                iou = b.intersection(a).area / b.union(a).area
                if iou > iou_thresh:
                    within = True
                    break
            if not within:
                kinda_final.append(rects_2[idx])
                final_polygons.append(b)
        final = []
        for idx_a, a in enumerate(final_polygons):
            within = False
            for idx_b, b in enumerate(final_polygons):
                iou = 0
                if idx_a != idx_b:
                    iou = b.intersection(a).area / b.union(a).area
                if iou > iou_thresh:
                    within = True
                    break
            if not within:
                final.append(kinda_final[idx_a])

        return final

    def rects_to_boxes(self, rects):
        boxes = []
        for rect in rects:
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            boxes.append(box)

        return boxes

    def crop_to_rect(self, src, rect):
        # Get center, size, and angle from rect
        center, size, theta = rect
        # Convert to int 
        center, size = tuple(map(int, center)), tuple(map(int, size))
        # Get rotation matrix for rectangle
        M = cv2.getRotationMatrix2D( center, theta, 1)
        # Perform rotation on src image
        dst = cv2.warpAffine(src, M, src.shape[:2])
        out = cv2.getRectSubPix(dst, size, center)
        return out

    def get_lego_size(self, dim):
        lego_size = []
        size_x, size_y  = dim
        for size in LegoSize:
            minim, maxim = size.value
            name = size.name
            if minim <= size_x <= maxim:
                lego_size.append(name)
            if minim <= size_y <= maxim:
                lego_size.append(name)
        return (lego_size[0], lego_size[1])


    def get_max_color(self, img):
        hist_hue = cv2.calcHist([img], [0], None, [180], [0,180])
        hist_sat = cv2.calcHist([img], [1], None, [256], [0,256])
        thresh_amt = 800
        _, _, _, max_hue = cv2.minMaxLoc(hist_hue)
        _, _, _, max_sat = cv2.minMaxLoc(hist_sat)
        max_sat = max_sat[1]
        max_hue = max_hue[1]
        for color in LegoColor:
            min_color, max_color, channel = color.value
            if channel == 1:
                if min_color <= max_sat <= max_color and \
                    hist_sat[max_sat] > thresh_amt:
                    return color.name
            if channel == 0:
                if min_color <= max_hue <= max_color and \
                    hist_hue[max_hue] > thresh_amt:
                    return color.name

    def detect(self, img):
        ori_img = img.copy()
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        ori_hsv = img_hsv.copy()
        h,s,v = cv2.split(img_hsv)

        rects_sat = self.rects_pipeline(s)
        rects_val = self.rects_pipeline(v)
        
        rects = self.remove_duplicate_rects(rects_sat, rects_val)
        boxes = self.rects_to_boxes(rects)
        colors = []
        sizes = []
        detected_amt = len(rects)
        for rect in rects:
            cropped = self.crop_to_rect(ori_hsv, rect)
            colors.append(self.get_max_color(cropped))
            sizes.append(self.get_lego_size(rect[1]))
        
        cv2.drawContours(ori_img,boxes,-1,(0,0,255),2)
        for idx in range(detected_amt):
            cv2.putText(ori_img, "{color}, {size1}x{size2}".format(color=colors[idx],\
                size1=sizes[idx][0], size2=sizes[idx][1]),\
                (tuple(boxes[idx][3])),\
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)

        items = list(zip(colors, sizes))
        return (ori_img, items)

if __name__ == "__main__":
    img = cv2.imread("test.png")

    detector = LegoDetector()
    result, items = detector.detect(img)
    cv2.imshow("result", result)
    cv2.waitKey()
