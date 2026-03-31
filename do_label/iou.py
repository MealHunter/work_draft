import numpy as np

def compute_iou(boxA, boxB, width, height):
    """
    boxA, boxB: [x, y, w, h]  左上角坐标 + 宽高
    width, height: 图像分辨率
    return: iou (float)
    """

    # boxA
    ax1 = max(0, boxA[0])
    ay1 = max(0, boxA[1])
    ax2 = min(width,  boxA[0] + boxA[2])
    ay2 = min(height, boxA[1] + boxA[3])

    # boxB
    bx1 = max(0, boxB[0])
    by1 = max(0, boxB[1])
    bx2 = min(width,  boxB[0] + boxB[2])
    by2 = min(height, boxB[1] + boxB[3])

    # intersection
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    # areas
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    # union
    union = area_a + area_b - inter_area + 1e-6

    return inter_area / union

if __name__ == "__main__":
    img_w, img_h = 2560, 1440

    boxA = [851, 347, 553, 171]  # x, y, w, h
    boxB = [431, 359, 619, 171]

    iou = compute_iou(boxA, boxB, img_w, img_h)
    print("IOU:", iou)