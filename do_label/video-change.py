import cv2
import os

def reencode_video(
    input_path,
    output_path,
    target_fps=30,
    target_size=None  # None 表示保持原分辨率，如 (1280, 720)
):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {input_path}")

    # 读取原视频信息
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if target_size is None:
        target_size = (width, height)

    print(f"源视频: {width}x{height}, fps={src_fps}")
    print(f"输出视频: {target_size[0]}x{target_size[1]}, fps={target_fps}")

    # H.264（Windows 上最稳）
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    writer = cv2.VideoWriter(
        output_path,
        fourcc,
        target_fps,
        target_size
    )

    if not writer.isOpened():
        raise RuntimeError("VideoWriter 打开失败，检查 OpenCV 是否支持 H.264")

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if target_size != (width, height):
            frame = cv2.resize(frame, target_size)

        writer.write(frame)
        frame_count += 1

    cap.release()
    writer.release()

    print(f"完成重编码，共处理 {frame_count} 帧")


if __name__ == "__main__":
    input_video = "分散.mp4"
    output_video = "分散_fixed.mp4"

    reencode_video(
        input_video,
        output_video,
        target_fps=30,
        target_size=None  # 改成 None 可保持原分辨率
    )
