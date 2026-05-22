"""
YOLO标签检测效果评估脚本（含黄色框/线检测）
对比两个文件夹中的.txt文件，对GT框在图片中裁剪区域检测是否含有黄色框/线，
含黄色的GT框视为也被预测到了，并排除与已有预测框重复计数的情况。
"""

import os
import cv2
import numpy as np
from collections import defaultdict


# ==========================
# 黄色框/线检测（复用 move_color.py 核心逻辑）
# ==========================

def build_yellow_mask(image):
    """构建黄色候选区域 mask"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_main = np.array([18, 110, 120], dtype=np.uint8)
    upper_main = np.array([38, 255, 255], dtype=np.uint8)
    lower_bright = np.array([20, 70, 180], dtype=np.uint8)
    upper_bright = np.array([40, 255, 255], dtype=np.uint8)

    mask_main = cv2.inRange(hsv, lower_main, upper_main)
    mask_bright = cv2.inRange(hsv, lower_bright, upper_bright)
    mask = cv2.bitwise_or(mask_main, mask_bright)

    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)


def contour_looks_like_box_line(contour, component_area):
    """判断连通域是否像黄色矩形框线，而非黄色主体"""
    if component_area < 25:
        return False

    x, y, w, h = cv2.boundingRect(contour)
    if w < 12 or h < 12:
        return False

    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return False

    bbox_area = float(w * h)
    fill_ratio = component_area / bbox_area
    thickness_score = component_area / (2.0 * (w + h))

    if fill_ratio > 0.35:
        return False
    if thickness_score > 5.0:
        return False

    approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
    if len(approx) < 4 or len(approx) > 8:
        return False

    return True


def has_yellow_in_region(image, x1, y1, x2, y2):
    """
    检测图片指定矩形区域内是否含有黄色框/线。
    image: BGR 图片
    x1, y1, x2, y2: 像素坐标（外接矩形）
    返回: True/False
    """
    H_img, W_img = image.shape[:2]
    # 裁剪区域，加一点余量以覆盖框线边缘
    pad = 5
    rx1 = max(0, int(x1) - pad)
    ry1 = max(0, int(y1) - pad)
    rx2 = min(W_img, int(x2) + pad)
    ry2 = min(H_img, int(y2) + pad)

    roi = image[ry1:ry2, rx1:rx2]
    if roi.size == 0:
        return False

    yellow_mask = build_yellow_mask(roi)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(yellow_mask, connectivity=8)

    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area < 25:
            continue

        component_mask = np.zeros_like(yellow_mask)
        component_mask[labels == label_id] = 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        contour = max(contours, key=cv2.contourArea)
        if contour_looks_like_box_line(contour, int(area)):
            return True

    return False


def load_image(image_path):
    """加载图片，兼容 Windows 中文路径"""
    try:
        data = np.fromfile(str(image_path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except OSError:
        return None


# ==========================
# YOLO 标签解析 & IoU 计算（与 match_txt.py 一致）
# ==========================

def parse_yolo_txt(txt_path):
    """解析YOLO格式标签文件"""
    boxes = []
    if not os.path.exists(txt_path):
        return boxes

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                cls = int(parts[0])
                cx = float(parts[1])
                cy = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
                boxes.append((cls, cx, cy, w, h))
            except ValueError:
                continue
    return boxes


def box_iou(box1, box2):
    """计算两个YOLO框的IoU"""
    if box1[0] != box2[0]:
        return 0.0

    b1_x1 = box1[1] - box1[3] / 2
    b1_y1 = box1[2] - box1[4] / 2
    b1_x2 = box1[1] + box1[3] / 2
    b1_y2 = box1[2] + box1[4] / 2

    b2_x1 = box2[1] - box2[3] / 2
    b2_y1 = box2[2] - box2[4] / 2
    b2_x2 = box2[1] + box2[3] / 2
    b2_y2 = box2[2] + box2[4] / 2

    inter_x1 = max(b1_x1, b2_x1)
    inter_y1 = max(b1_y1, b2_y1)
    inter_x2 = min(b1_x2, b2_x2)
    inter_y2 = min(b1_y2, b2_y2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    box1_area = box1[3] * box1[4]
    box2_area = box2[3] * box2[4]

    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0.0

    return inter_area / union_area


def match_boxes(gt_boxes, pred_boxes, iou_threshold=0.5):
    """匹配预测框和真实框，返回 (tp, matched_gt_idx, matched_pred_idx)"""
    tp = 0
    matched_gt = set()
    matched_pred = set()

    for i, gt_box in enumerate(gt_boxes):
        for j, pred_box in enumerate(pred_boxes):
            if j in matched_pred:
                continue
            iou = box_iou(gt_box, pred_box)
            if iou >= iou_threshold:
                tp += 1
                matched_gt.add(i)
                matched_pred.add(j)
                break

    return tp, matched_gt, matched_pred


def gt_box_has_yellow(image, gt_box, W_img, H_img):
    """
    判断某个GT框对应的图片区域内是否含有黄色框/线。
    gt_box: (cls, cx, cy, w, h) 归一化坐标
    返回: True/False
    """
    # 归一化坐标转像素坐标
    cx, cy, bw, bh = gt_box[1], gt_box[2], gt_box[3], gt_box[4]
    x1 = (cx - bw / 2) * W_img
    y1 = (cy - bh / 2) * H_img
    x2 = (cx + bw / 2) * W_img
    y2 = (cy + bh / 2) * H_img

    return has_yellow_in_region(image, x1, y1, x2, y2)


def find_yellow_gt_indices(image, gt_boxes, W_img, H_img):
    """
    遍历所有GT框，检测哪些GT框区域内含有黄色框/线。
    返回: 含黄色的GT框索引集合
    """
    yellow_gt_indices = set()
    for i, gt_box in enumerate(gt_boxes):
        if gt_box_has_yellow(image, gt_box, W_img, H_img):
            yellow_gt_indices.add(i)
    return yellow_gt_indices


def find_image_path(image_folder, txt_filename):
    """根据txt文件名找到对应的图片路径"""
    base_name = os.path.splitext(txt_filename)[0]
    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
        img_path = os.path.join(image_folder, base_name + ext)
        if os.path.exists(img_path):
            return img_path
    return None


# ==========================
# 主评估逻辑
# ==========================

def evaluate_folder(gt_folder, pred_folder, image_folder, iou_threshold=0.5):
    """
    评估两个文件夹的标签文件，同时检测GT框区域内是否含有黄色框/线。

    匹配逻辑：
    1. 解析 GT 标签和 Pred 标签
    2. 对每个GT框，在图片中裁剪其区域，检测是否含黄色框/线
    3. 含黄色的GT框视为"也被预测到了"，将其自身加入Pred列表
    4. 二级判断：先用Pred框与GT匹配，含黄色但已被Pred匹配上的GT框属于重复计数，不再额外加入
    5. 仅将"含黄色且未被Pred匹配"的GT框加入Pred列表，重新匹配统计
    """
    gt_files = set(f for f in os.listdir(gt_folder) if f.endswith('.txt'))
    pred_files = set(f for f in os.listdir(pred_folder) if f.endswith('.txt'))

    common_files = gt_files & pred_files
    only_gt = gt_files - pred_files
    only_pred = pred_files - gt_files

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt_boxes = 0
    detected_images = 0
    total_images = len(common_files)

    # 黄色框统计
    total_yellow_gt = 0          # 含黄色的GT框总数
    total_yellow_duplicate = 0   # 含黄色但已被Pred匹配（重复计数，不加）
    total_yellow_added = 0       # 含黄色且未重复，实际加入Pred的

    details = []

    for filename in sorted(common_files):
        gt_path = os.path.join(gt_folder, filename)
        pred_path = os.path.join(pred_folder, filename)

        gt_boxes = parse_yolo_txt(gt_path)
        pred_boxes = parse_yolo_txt(pred_path)

        # ========== 检测GT框区域内的黄色框/线 ==========
        img_path = find_image_path(image_folder, filename)
        yellow_gt_indices = set()  # 含黄色的GT框索引

        if img_path and gt_boxes:
            image = load_image(img_path)
            if image is not None:
                H_img, W_img = image.shape[:2]
                yellow_gt_indices = find_yellow_gt_indices(image, gt_boxes, W_img, H_img)

        # ========== 第一轮匹配：Pred框 vs GT框 ==========
        tp1, matched_gt1, matched_pred1 = match_boxes(gt_boxes, pred_boxes, iou_threshold)

        # ========== 二级判断：含黄色的GT框中，哪些已被Pred匹配（重复），哪些未被匹配（需加入） ==========
        yellow_duplicate = yellow_gt_indices & matched_gt1   # 含黄色且已被Pred匹配 → 重复，不加
        yellow_to_add = yellow_gt_indices - matched_gt1      # 含黄色且未被Pred匹配 → 加入Pred列表

        total_yellow_gt += len(yellow_gt_indices)
        total_yellow_duplicate += len(yellow_duplicate)
        total_yellow_added += len(yellow_to_add)

        # 将"含黄色且未重复"的GT框加入Pred列表
        extra_pred_boxes = [gt_boxes[i] for i in yellow_to_add]
        extended_pred_boxes = pred_boxes + extra_pred_boxes

        # ========== 第二轮匹配：扩展后的Pred框 vs GT框 ==========
        total_gt_boxes += len(gt_boxes)

        tp, matched_gt, matched_pred = match_boxes(gt_boxes, extended_pred_boxes, iou_threshold)
        fp = len(extended_pred_boxes) - len(matched_pred)
        fn = len(gt_boxes) - len(matched_gt)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        image_detected = len(matched_gt) > 0 if len(gt_boxes) > 0 else (len(extended_pred_boxes) > 0)
        if image_detected:
            detected_images += 1

        details.append({
            'filename': filename,
            'gt_count': len(gt_boxes),
            'pred_count': len(pred_boxes),
            'yellow_gt': len(yellow_gt_indices),
            'yellow_duplicate': len(yellow_duplicate),
            'yellow_added': len(yellow_to_add),
            'extended_pred_count': len(extended_pred_boxes),
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'detected': image_detected
        })

    # 纯 GT 文件也算漏检图片
    total_images += len(only_gt)

    return {
        'common_count': len(common_files),
        'only_gt_count': len(only_gt),
        'only_pred_count': len(only_pred),
        'total_tp': total_tp,
        'total_fp': total_fp,
        'total_fn': total_fn,
        'total_gt_boxes': total_gt_boxes,
        'detected_images': detected_images,
        'total_images': total_images,
        'total_yellow_gt': total_yellow_gt,
        'total_yellow_duplicate': total_yellow_duplicate,
        'total_yellow_added': total_yellow_added,
        'details': details,
        'only_gt_files': sorted(only_gt),
        'only_pred_files': sorted(only_pred)
    }


def print_report(result, iou_threshold=0.5):
    """打印评估报告"""
    print("=" * 60)
    print("YOLO标签检测效果评估报告（含黄色框/线检测）")
    print("=" * 60)

    # 文件统计
    print(f"\n【文件统计】")
    print(f"  同名文件数量: {result['common_count']}")
    print(f"  仅GT有文件数量: {result['only_gt_count']}")
    print(f"  仅Pred有文件数量: {result['only_pred_count']}")

    # 黄色框统计
    print(f"\n【GT框黄色检测统计】")
    print(f"  含黄色的GT框总数: {result['total_yellow_gt']}")
    print(f"  已被Pred匹配(重复,不额外加): {result['total_yellow_duplicate']}")
    print(f"  未被Pred匹配(加入统计): {result['total_yellow_added']}")

    # 框级别统计
    print(f"\n【框级别统计】(IoU阈值={iou_threshold})")
    print(f"  总TP(正检数量): {result['total_tp']}")
    print(f"  总FP(误检数量): {result['total_fp']}")
    print(f"  总FN(漏检数量): {result['total_fn']}")

    total_pred = result['total_tp'] + result['total_fp']
    total_gt = result['total_tp'] + result['total_fn']

    if total_pred > 0:
        precision = result['total_tp'] / total_pred
    else:
        precision = 0.0

    if total_gt > 0:
        recall = result['total_tp'] / total_gt
    else:
        recall = 0.0

    if result['total_gt_boxes'] > 0:
        box_miss_rate = result['total_fn'] / result['total_gt_boxes']
    else:
        box_miss_rate = 0.0

    print(f"  Precision(准确度): {precision:.4f} ({result['total_tp']}/{total_pred})")
    print(f"  Recall(召回率/检出率): {recall:.4f} ({result['total_tp']}/{total_gt})")
    print(f"  框漏检率: {box_miss_rate:.4f} ({result['total_fn']}/{result['total_gt_boxes']})")

    # 图片级别统计
    print(f"\n【图片级别统计】")
    print(f"  检出图片数量: {result['detected_images']}")
    print(f"  总图片数量(含仅GT): {result['total_images']}")

    if result['total_images'] > 0:
        image_recall = result['detected_images'] / result['total_images']
        image_miss_rate = 1 - image_recall
    else:
        image_recall = 0.0
        image_miss_rate = 0.0

    print(f"  图片召回率(检出率): {image_recall:.4f} ({result['detected_images']}/{result['total_images']})")
    print(f"  漏检率: {image_miss_rate:.4f}")

    # 逐图片详情（含黄色GT框的图片）
    yellow_details = [d for d in result['details'] if d['yellow_gt'] > 0]
    if yellow_details:
        print(f"\n【含黄色GT框的图片详情】({len(yellow_details)}张)")
        print(f"  {'文件名':<30} {'GT':>4} {'Pred':>4} {'黄GT':>4} {'重复':>4} {'加入':>4} {'TP':>4} {'FP':>4} {'FN':>4}")
        print(f"  {'-'*82}")
        for d in yellow_details[:30]:
            print(f"  {d['filename']:<30} {d['gt_count']:>4} {d['pred_count']:>4} {d['yellow_gt']:>4} "
                  f"{d['yellow_duplicate']:>4} {d['yellow_added']:>4} {d['tp']:>4} {d['fp']:>4} {d['fn']:>4}")
        if len(yellow_details) > 30:
            print(f"  ... 还有{len(yellow_details) - 30}张")

    # 仅GT有/仅Pred有的文件列表
    if result['only_gt_files']:
        print(f"\n【仅GT有的文件】({len(result['only_gt_files'])}个)")
        for f in result['only_gt_files'][:20]:
            print(f"    {f}")
        if len(result['only_gt_files']) > 20:
            print(f"    ... 还有{len(result['only_gt_files']) - 20}个")

    if result['only_pred_files']:
        print(f"\n【仅Pred有的文件】({len(result['only_pred_files'])}个)")
        for f in result['only_pred_files'][:20]:
            print(f"    {f}")
        if len(result['only_pred_files']) > 20:
            print(f"    ... 还有{len(result['only_pred_files']) - 20}个")

    print("\n" + "=" * 60)

    return {
        'precision': precision,
        'recall': recall,
        'box_miss_rate': box_miss_rate,
        'image_recall': image_recall,
        'image_miss_rate': image_miss_rate
    }


if __name__ == "__main__":
    # 配置路径
    gt_folder = r"C:\Users\DELL\Desktop\误报漏报视频\labels"        # 真实标签文件夹
    pred_folder = r"C:\Users\DELL\Desktop\误报漏报视频\output"       # 预测标签文件夹
    image_folder = r"C:\Users\DELL\Desktop\误报漏报视频\images"      # 图片文件夹（用于黄色框检测）
    iou_threshold = 0.5                                            # IoU匹配阈值

    # 运行评估
    result = evaluate_folder(gt_folder, pred_folder, image_folder, iou_threshold)
    metrics = print_report(result, iou_threshold)