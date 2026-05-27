import cv2 as cv
import numpy as np
import os
import shutil

# ============================================================
# 模式切换：pick = 取色模式（查看黄色框HSV值），detect = 检测移动模式
# ============================================================
MODE = "detect"

# 配置路径
image_dir = r"E:\pack\dataset\img"
move_dir = r"E:\pack\dataset\move"

# 黄色HSV范围（取色模式下根据输出结果调整这里）
HSV_LOWER = np.array([20, 90, 100])
HSV_UPPER = np.array([40, 255, 255])

# 黄色像素占比阈值
YELLOW_RATIO_THRESHOLD = 0.001

# 取色模式用的图片路径
PICK_IMAGE = r"E:\pack\dataset\img\pack2_00050.jpg"


# ======================== 取色模式 ========================
def pick_color():
    """打开图片，鼠标移动显示BGR和HSV值，用于确定黄色框的HSV范围"""
    img = cv.imread(PICK_IMAGE)
    if img is None:
        print(f"读取失败: {PICK_IMAGE}")
        return

    hsv_img = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    def on_mouse(event, x, y, flags, param):
        if event == cv.EVENT_MOUSEMOVE:
            b, g, r = img[y, x]
            h, s, v = hsv_img[y, x]
            display = img.copy()
            text = f"BGR:({r},{g},{b})  HSV:({h},{s},{v})  pos:({x},{y})"
            cv.putText(display, text, (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv.rectangle(display, (10, 40), (60, 90), (int(b), int(g), int(r)), -1)
            cv.imshow("pick_color", display)
        elif event == cv.EVENT_LBUTTONDOWN:
            b, g, r = img[y, x]
            h, s, v = hsv_img[y, x]
            print(f"pos:({x},{y})  BGR:({r},{g},{b})  HSV:({h},{s},{v})")

    print("移动鼠标查看颜色，左键点击打印HSV值到终端")
    print("多点击黄色框区域，观察H/S/V的范围，然后修改 HSV_LOWER 和 HSV_UPPER")
    cv.namedWindow("pick_color")
    cv.setMouseCallback("pick_color", on_mouse)
    cv.imshow("pick_color", img)
    cv.waitKey(0)
    cv.destroyAllWindows()


# ======================== 检测移动模式 ========================
def has_yellow_box(img):
    """检测图片中是否包含黄色区域"""
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, HSV_LOWER, HSV_UPPER)
    # 开运算去噪
    kernel = np.ones((5, 5), np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
    yellow_ratio = np.sum(mask > 0) / mask.size
    return yellow_ratio > YELLOW_RATIO_THRESHOLD


def detect_and_move():
    if not os.path.exists(image_dir):
        print(f"图片文件夹不存在: {image_dir}")
        return

    os.makedirs(move_dir, exist_ok=True)

    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
    files = [f for f in os.listdir(image_dir) if f.lower().endswith(exts)]
    if not files:
        print("image文件夹中没有图片")
        return

    moved = 0
    for fname in files:
        fpath = os.path.join(image_dir, fname)
        img = cv.imread(fpath)
        if img is None:
            print(f"读取失败，跳过: {fname}")
            continue

        if has_yellow_box(img):
            shutil.move(fpath, os.path.join(move_dir, fname))
            print(f"检测到黄色框，已移动: {fname}")
            moved += 1
        else:
            print(f"未检测到黄色框: {fname}")

    print(f"\n完成！共处理 {len(files)} 张图片，移动 {moved} 张")


if __name__ == "__main__":
    if MODE == "pick":
        pick_color()
    else:
        detect_and_move()