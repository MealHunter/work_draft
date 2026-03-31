import cv2
import numpy as np

def jpg_to_nv12(jpg_path, yuv_path):
    img = cv2.imread(jpg_path)
    if img is None:
        raise RuntimeError(f"Failed to load image: {jpg_path}")

    h, w, _ = img.shape
    h -= h % 2
    w -= w % 2
    img = img[:h, :w]

    # BGR -> I420 (YUV420P)
    yuv_i420 = cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420)

    # Y plane
    y = yuv_i420[0:h, :w]

    # U plane
    u = yuv_i420[h:h + h//4, :w//2]

    # V plane
    v = yuv_i420[h + h//4:h + h//2, :w//2]

    # NV12 UV plane
    uv = np.zeros((h//2, w), dtype=np.uint8)
    # 把 U/V 上下复制一行填充到 h//2
    for i in range(h//2):
        uv[i, 0::2] = u[i//2]
        uv[i, 1::2] = v[i//2]

    # 拼接 Y + UV
    nv12 = np.vstack((y, uv))

    # 保存 NV12
    with open(yuv_path, "wb") as f:
        f.write(nv12.tobytes())

    print(f"Saved NV12: {yuv_path} ({w}x{h})")


def visualize_nv12(nv12_path, w, h):
    with open(nv12_path, "rb") as f:
        nv12 = np.frombuffer(f.read(), dtype=np.uint8)
    y = nv12[:w*h].reshape((h, w))
    uv = nv12[w*h:].reshape((h//2, w))
    nv12_img = np.vstack((y, uv))
    bgr = cv2.cvtColor(nv12_img, cv2.COLOR_YUV2BGR_NV12)
    cv2.imshow("NV12->BGR", bgr)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    jpg_path = r"C:/Users/DELL/Desktop/fsdownload/test_fish.jpg"
    yuv_path = r"C:/Users/DELL/Desktop/fsdownload/test_fish.yuv"
    jpg_to_nv12(jpg_path, yuv_path)
    visualize_nv12(yuv_path, 900, 632)
