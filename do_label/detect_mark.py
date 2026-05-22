#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
水印检测脚本
检测图片中的水印位置和特征
"""

import cv2
import numpy as np
from pathlib import Path


class WatermarkDetector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.height, self.width = self.gray.shape

    def detect_by_edge(self, threshold1=50, threshold2=150):
        """基于边缘检测的水印检测"""
        edges = cv2.Canny(self.gray, threshold1, threshold2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        watermark_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:
                x, y, w, h = cv2.boundingRect(contour)
                watermark_regions.append({
                    'method': 'edge_detection',
                    'bbox': (x, y, w, h),
                    'area': area
                })

        return watermark_regions

    def detect_by_frequency(self):
        """基于频域分析的水印检测"""
        dft = cv2.dft(np.float32(self.gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        magnitude = cv2.magnitude(dft_shift[:,:,0], dft_shift[:,:,1])
        magnitude = np.log(magnitude + 1)
        magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        _, thresh = cv2.threshold(magnitude, 200, 255, cv2.THRESH_BINARY)

        return {
            'method': 'frequency_domain',
            'magnitude_spectrum': magnitude,
            'high_frequency_regions': thresh
        }

    def detect_by_intensity(self, alpha_threshold=0.7):
        """基于亮度/透明度分析的水印检测"""
        mean_intensity = np.mean(self.gray)
        std_intensity = np.std(self.gray)

        anomaly_mask = np.abs(self.gray - mean_intensity) > (std_intensity * alpha_threshold)
        anomaly_mask = anomaly_mask.astype(np.uint8) * 255

        kernel = np.ones((5,5), np.uint8)
        anomaly_mask = cv2.morphologyEx(anomaly_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(anomaly_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        watermark_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                watermark_regions.append({
                    'method': 'intensity_analysis',
                    'bbox': (x, y, w, h),
                    'area': area
                })

        return watermark_regions

    def detect_by_template(self, template_path):
        """基于模板匹配的水印检测"""
        if not Path(template_path).exists():
            return None

        template = cv2.imread(str(template_path), 0)
        if template is None:
            return None

        result = cv2.matchTemplate(self.gray, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)

        watermark_regions = []
        for pt in zip(*locations[::-1]):
            watermark_regions.append({
                'method': 'template_matching',
                'bbox': (pt[0], pt[1], template.shape[1], template.shape[0]),
                'confidence': result[pt[1], pt[0]]
            })

        return watermark_regions

    def visualize_results(self, results, output_path=None):
        """可视化检测结果"""
        result_image = self.image.copy()

        for result in results:
            if 'bbox' in result:
                x, y, w, h = result['bbox']
                cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                method = result.get('method', 'unknown')
                cv2.putText(result_image, method, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if output_path:
            cv2.imwrite(str(output_path), result_image)

        return result_image

    def detect_all(self):
        """综合所有检测方法"""
        print(f"正在检测图片: {self.image_path}")
        print(f"图片尺寸: {self.width}x{self.height}")

        all_results = []

        print("\n1. 边缘检测方法...")
        edge_results = self.detect_by_edge()
        all_results.extend(edge_results)
        print(f"   检测到 {len(edge_results)} 个可能的水印区域")

        print("\n2. 频域分析方法...")
        freq_result = self.detect_by_frequency()
        print(f"   频域分析完成")

        print("\n3. 亮度分析方法...")
        intensity_results = self.detect_by_intensity()
        all_results.extend(intensity_results)
        print(f"   检测到 {len(intensity_results)} 个可能的水印区域")

        return all_results


def main():
    image_path = Path(__file__).parent.parent / "images" / "mark.png"

    if not image_path.exists():
        print(f"错误: 图片文件不存在 - {image_path}")
        return

    detector = WatermarkDetector(image_path)
    results = detector.detect_all()

    print(f"\n总共检测到 {len(results)} 个可能的水印区域")

    for i, result in enumerate(results, 1):
        print(f"\n区域 {i}:")
        print(f"  方法: {result['method']}")
        if 'bbox' in result:
            x, y, w, h = result['bbox']
            print(f"  位置: ({x}, {y})")
            print(f"  大小: {w}x{h}")
        if 'area' in result:
            print(f"  面积: {result['area']}")
        if 'confidence' in result:
            print(f"  置信度: {result['confidence']:.2f}")

    output_path = image_path.parent / "mark_detected.png"
    result_image = detector.visualize_results(results, output_path)
    print(f"\n检测结果已保存到: {output_path}")

    cv2.imshow("Watermark Detection", result_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
