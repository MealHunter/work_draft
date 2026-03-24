"""
YOLO标签检测效果评估脚本
对比两个文件夹中的.txt文件，计算IoU并统计检出效果
"""

import os
import numpy as np
from collections import defaultdict


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
    """
    计算两个YOLO框的IoU
    box格式: (class, cx, cy, w, h) - 归一化坐标
    返回: IoU值
    """
    # 如果类别不同，IoU为0
    if box1[0] != box2[0]:
        return 0.0
    
    # 转换为 (x1, y1, x2, y2) 格式
    b1_x1 = box1[1] - box1[3] / 2
    b1_y1 = box1[2] - box1[4] / 2
    b1_x2 = box1[1] + box1[3] / 2
    b1_y2 = box1[2] + box1[4] / 2
    
    b2_x1 = box2[1] - box2[3] / 2
    b2_y1 = box2[2] - box2[4] / 2
    b2_x2 = box2[1] + box2[3] / 2
    b2_y2 = box2[2] + box2[4] / 2
    
    # 计算交集区域
    inter_x1 = max(b1_x1, b2_x1)
    inter_y1 = max(b1_y1, b2_y1)
    inter_x2 = min(b1_x2, b2_x2)
    inter_y2 = min(b1_y2, b2_y2)
    
    # 计算交集面积
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    
    # 计算各自面积
    box1_area = box1[3] * box1[4]
    box2_area = box2[3] * box2[4]
    
    # 计算并集面积
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area


def match_boxes(gt_boxes, pred_boxes, iou_threshold=0.5):
    """
    匹配预测框和真实框
    返回: (tp, matched_gt_idx, matched_pred_idx)
    """
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


def evaluate_folder(gt_folder, pred_folder, iou_threshold=0.5):
    """
    评估两个文件夹的标签文件
    """
    # 获取所有txt文件
    gt_files = set(f for f in os.listdir(gt_folder) if f.endswith('.txt'))
    pred_files = set(f for f in os.listdir(pred_folder) if f.endswith('.txt'))
    
    # 统计同名文件
    common_files = gt_files & pred_files
    only_gt = gt_files - pred_files
    only_pred = pred_files - gt_files
    
    # 统计变量
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt_boxes = 0
    detected_images = 0
    total_images = len(common_files)
    
    # 详细结果记录
    details = []
    
    # 逐个文件对比
    for filename in sorted(common_files):
        gt_path = os.path.join(gt_folder, filename)
        pred_path = os.path.join(pred_folder, filename)
        
        gt_boxes = parse_yolo_txt(gt_path)
        pred_boxes = parse_yolo_txt(pred_path)
        
        total_gt_boxes += len(gt_boxes)
        
        # 匹配框
        tp, matched_gt, matched_pred = match_boxes(gt_boxes, pred_boxes, iou_threshold)
        fp = len(pred_boxes) - len(matched_pred)
        fn = len(gt_boxes) - len(matched_gt)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        # 图片层面检出（至少有一个GT框被匹配）
        image_detected = len(matched_gt) > 0 if len(gt_boxes) > 0 else (len(pred_boxes) > 0)
        if image_detected:
            detected_images += 1
        
        details.append({
            'filename': filename,
            'gt_count': len(gt_boxes),
            'pred_count': len(pred_boxes),
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'detected': image_detected
        })
    
    # 统计只有GT或只有Pred的文件
    total_images += len(only_gt)  # 纯漏检图片
    
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
        'details': details,
        'only_gt_files': sorted(only_gt),
        'only_pred_files': sorted(only_pred)
    }


def print_report(result, iou_threshold=0.5):
    """打印评估报告"""
    print("=" * 60)
    print("YOLO标签检测效果评估报告")
    print("=" * 60)
    
    # 文件统计
    print(f"\n【文件统计】")
    print(f"  同名文件数量: {result['common_count']}")
    print(f"  仅GT有文件数量: {result['only_gt_count']}")
    print(f"  仅Pred有文件数量: {result['only_pred_count']}")
    
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
    gt_folder = r"D:\yyb\dataset\images_640\txt"           # 真实标签文件夹
    pred_folder = r"D:\yyb\dataset\images_640\outputs3-24"        # 预测标签文件夹
    iou_threshold = 0.5                      # IoU匹配阈值
    
    # 运行评估
    result = evaluate_folder(gt_folder, pred_folder, iou_threshold)
    metrics = print_report(result, iou_threshold)
