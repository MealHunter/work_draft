FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3-pip \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/*

# 复制整个项目目录
COPY ultralytics-8.3.57 /app/ultralytics

# 设置 PYTHONPATH，让项目可以正确导入
ENV PYTHONPATH=/app:$PYTHONPATH

# 安装项目依赖（editable 模式，包含 export 支持 ONNX）
RUN pip install --no-cache-dir -e /app/ultralytics[export]

# 创建输出目录
RUN mkdir -p /app/output /workdir/share/dataset /workdir/share/onnx_model

WORKDIR /app

# 默认命令
CMD ["bash"]
