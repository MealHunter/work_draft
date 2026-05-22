#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
无痕去除图片中的黄色框。

改进策略：
1. 先在 HSV 空间检测黄色像素；
2. 再通过连通域 + 细线/矩形特征过滤，仅保留疑似黄色标注框线；
3. 仅对细线区域做轻量膨胀；
4. 使用 Telea inpaint 去除框线，尽量减少对主体内容的破坏。
"""

from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def read_image_unicode(image_path: Path) -> Optional[np.ndarray]:
    """兼容 Windows 中文路径读取图片。"""
    try:
        data = np.fromfile(str(image_path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except OSError:
        return None


def write_image_unicode(image_path: Path, image: np.ndarray) -> bool:
    """兼容 Windows 中文路径写入图片。"""
    ext = image_path.suffix.lower() or ".jpg"
    success, encoded = cv2.imencode(ext, image)
    if not success:
        return False
    try:
        encoded.tofile(str(image_path))
    except OSError:
        return False
    return True


def build_yellow_mask(image: np.ndarray) -> np.ndarray:
    """构建更保守的黄色候选区域。"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_main = np.array([18, 110, 120], dtype=np.uint8)
    upper_main = np.array([38, 255, 255], dtype=np.uint8)
    lower_bright = np.array([20, 70, 180], dtype=np.uint8)
    upper_bright = np.array([40, 255, 255], dtype=np.uint8)

    mask_main = cv2.inRange(hsv, lower_main, upper_main)
    mask_bright = cv2.inRange(hsv, lower_bright, upper_bright)
    mask = cv2.bitwise_or(mask_main, mask_bright)

    # 轻量闭运算，仅连接被压缩噪声打断的细线，不做大范围膨胀。
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)


def contour_looks_like_box_line(contour: np.ndarray, component_area: int) -> bool:
    """判断连通域是否像一个黄色矩形框线，而不是黄色主体。"""
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

    # 细线框通常面积占包围盒比例较低，且线条厚度较薄。
    if fill_ratio > 0.35:
        return False
    if thickness_score > 5.0:
        return False

    approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
    if len(approx) < 4 or len(approx) > 8:
        return False

    return True


def extract_box_line_mask(yellow_mask: np.ndarray) -> np.ndarray:
    """从黄色候选区域中筛出疑似矩形框线。"""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(yellow_mask, connectivity=8)
    filtered_mask = np.zeros_like(yellow_mask)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area < 25 or area > 12000:
            continue

        component_mask = np.zeros_like(yellow_mask)
        component_mask[labels == label] = 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        contour = max(contours, key=cv2.contourArea)
        if contour_looks_like_box_line(contour, int(area)):
            filtered_mask[labels == label] = 255

    # 只做极轻量扩张，覆盖抗锯齿边缘，避免吞掉主体。
    kernel = np.ones((3, 3), np.uint8)
    return cv2.dilate(filtered_mask, kernel, iterations=1)


def remove_yellow_boxes(image: np.ndarray) -> np.ndarray:
    """去除图片中的黄色框，并尽量减少画面变形。"""
    yellow_mask = build_yellow_mask(image)
    box_mask = extract_box_line_mask(yellow_mask)

    if cv2.countNonZero(box_mask) == 0:
        return image.copy()

    # Telea 对细线、划痕类目标通常更自然，半径也控制得更小。
    return cv2.inpaint(image, box_mask, inpaintRadius=2, flags=cv2.INPAINT_TELEA)


def process_directory(input_dir: str, output_dir: Optional[str] = None):
    """批量处理文件夹中的图片。"""
    input_path = Path(input_dir)
    output_path = input_path / "removed" if output_dir is None else Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    image_files = [file for file in input_path.iterdir() if file.suffix.lower() in extensions]

    if not image_files:
        print(f"未在 {input_dir} 中找到图片文件")
        return

    print(f"找到 {len(image_files)} 张图片，开始处理...")

    for img_file in image_files:
        print(f"处理: {img_file.name} ...", end=" ")
        image = read_image_unicode(img_file)
        if image is None:
            print("无法读取，跳过")
            continue

        result = remove_yellow_boxes(image)
        out_file = output_path / img_file.name
        if write_image_unicode(out_file, result):
            print("完成")
        else:
            print("写入失败，跳过")

    print(f"\n所有图片已保存到: {output_path}")


if __name__ == "__main__":
    img_dir = Path("C:/Users/DELL/Desktop/误报漏报视频/images")

    if not img_dir.exists():
        print(f"错误: 图片文件夹不存在 - {img_dir}")
    else:
        process_directory(str(img_dir))
