# YOLOv8 Docker 训练与导出项目

基于 Docker Compose 的自动化流水线项目，用于监听数据集变化、执行 YOLOv8 训练、导出 ONNX 模型，并调用 Goke 工具链完成模型转换。

## 项目概述

当前项目包含两个常驻服务：

1. **yolov8**：监听宿主机共享目录中的数据集变化，触发训练并导出 ONNX。
2. **goke7605**：监听 ONNX 输出目录中的新模型，调用镜像内工具链完成 `.xmm` 转换。

## 当前目录结构

```text
train_and_export/
├── docker-compose.yml
├── README.md
├── yolov8/
│   ├── Dockerfile
│   ├── Dockerfile.txt
│   ├── .dockerignore
│   ├── yolov8_run.sh
│   └── ultralytics-8.3.57/
├── export/
│   ├── Dockerfile
│   ├── Dockerfile.txt
│   ├── README.txt
│   ├── goke_run.sh
│   ├── AI_TOOLCHAIN_V020_V3010_*.tar.gz
│   └── opensource_model_zoo.v020.tar.gz
└── train/
    ├── train.py
    └── export.py
```

## 宿主机共享目录

容器会挂载以下宿主机目录：

```text
/home/yang.yongbiao/workdir/share:/root/share
```

建议宿主机准备如下结构：

```text
/home/yang.yongbiao/workdir/share/
├── dataset/                 # 训练数据集，需包含 data.yaml
├── onnx_model/              # YOLO 导出的 ONNX 输出目录
├── goke_model/              # Goke 转换后的 xmm 输出目录
└── train/
    ├── train.py             # 训练脚本（可直接修改）
    └── export.py            # 导出脚本（可直接修改）
```

## Compose 启动方式

在项目根目录直接执行：

```bash
docker compose up -d --build
```

停止服务：

```bash
docker compose down
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker logs -f yolov8
docker logs -f goke7605
```

## docker-compose 服务说明

### yolov8

- 镜像名：`yolov8_image`
- 构建上下文：`./yolov8`
- 启动命令：

```yaml
command: bash /root/yolov8_run.sh
```

- 数据挂载：

```text
/home/yang.yongbiao/workdir/share:/root/share
```

### goke7605

- 镜像名：`ubuntu18.04:goke7605`
- 构建上下文：`./export`
- 启动命令：

```yaml
command: bash /root/goke_run.sh
```

- 数据挂载：

```text
/home/yang.yongbiao/workdir/share:/root/share
```

## 服务运行逻辑

## 1. yolov8 服务

入口脚本：

```text
yolov8/yolov8_run.sh
```

运行逻辑：

- 监听 `/root/share/dataset`
- 当检测到 `*.yaml` 文件写入或移动完成时触发训练
- 调用宿主机训练脚本：

```bash
python /root/share/train/train.py \
    --data /root/share/dataset/data.yaml \
    --project /root/share/onnx_model \
    --name latest \
    --epochs 50 \
    --batch 32
```

- 训练完成后调用宿主机导出脚本：

```bash
python /root/share/train/export.py \
    --model /root/share/onnx_model/latest/weights/best.pt \
    --format onnx \
    --imgsz 360 640
```

## 2. goke7605 服务

入口脚本：

```text
export/goke_run.sh
```

运行逻辑：

- 监听 `/root/share/onnx_model`
- 检测到新的 `.onnx` 文件后，根据模型名匹配工具链目录
- 默认工具链目录：

```text
/xmedia/opensource_model_zoo
```

- 执行：

```bash
python build.py
```

- 转换后的 `.xmm` 文件输出到：

```text
/root/share/goke_model
```

## 自定义修改说明

### 修改训练逻辑

直接编辑宿主机目录中的文件即可，无需重建镜像：

```text
/home/yang.yongbiao/workdir/share/train/train.py
/home/yang.yongbiao/workdir/share/train/export.py
```

### 修改容器入口逻辑

编辑以下文件后，需要重新构建镜像：

```text
yolov8/yolov8_run.sh
export/goke_run.sh
```

修改后执行：

```bash
docker compose up -d --build
```

## 常用命令

```bash
# 构建并启动
docker compose up -d --build

# 仅启动已有容器
docker compose up -d

# 查看容器状态
docker compose ps

# 查看日志
docker logs -f yolov8
docker logs -f goke7605

# 进入容器
docker exec -it yolov8 bash
docker exec -it goke7605 bash

# 停止服务
docker compose down
```

## 注意事项

1. `yolov8` 服务依赖 NVIDIA 运行时。
2. `train.py` 和 `export.py` 保留在宿主机共享目录中，方便直接修改。
3. `goke7605` 依赖 `export/` 目录中的工具链压缩包在构建时可用。
4. 如果在 Windows 中维护项目，可使用占位文件；在 Linux 实际构建时需替换为真实工具链内容。
5. `docker compose` 新版不再需要 `version` 字段，建议不要在 `docker-compose.yml` 中保留。

## 许可证

本项目仅供学习和内部使用。
