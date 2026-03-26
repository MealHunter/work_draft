# YOLOv8 Docker 训练与导出项目

基于 Docker Compose 的自动化流水线项目，用于监听数据集变化、执行 YOLOv8 训练、导出 ONNX 模型，并调用 Goke 工具链完成模型转换。

## 项目概述

当前项目包含两个常驻服务：

1. **yolov8**：监听 `/share/dataset` 目录中的 `*.yaml` 变更，触发训练并导出 ONNX。
2. **goke7605**：监听 `/share/onnx_model` 目录中的 `.onnx` 文件，调用工具链转换为 `.xmm`。

## 架构

```
┌─────────────────┐     ┌─────────────────┐
│   yolov8 容器   │     │  goke7605 容器  │
│                 │     │                 │
│ - 监听数据集    │     │ - 监听 ONNX     │
│ - 执行训练      │────▶│ - 执行模型转换  │
│ - 导出 ONNX     │     │ - 输出 XMM      │
└─────────────────┘     └─────────────────┘
         │                       │
         └──────────┬────────────┘
                    │
             /workdir/share
```

## 目录结构

```
docker/
├── docker-compose.yml   # Compose 配置
├── yolov8/
│   ├── Dockerfile       # YOLOv8 镜像
│   └── .dockerignore
├── export/
│   ├── Dockerfile       # Goke 工具链构建镜像示例
│   ├── Dockerfile.txt   # 基于预制镜像的简化示例
│   └── README.txt
├── yolov8_run.sh        # 训练与导出入口脚本
└── goke_run.sh          # ONNX 转 xmm 入口脚本
```

## 环境要求

- Docker
- Docker Compose
- NVIDIA GPU（用于 YOLOv8 训练）
- NVIDIA Container Toolkit
- 主机存在共享目录：`/workdir/share`

建议在共享目录中准备以下结构：

```text
/workdir/share/
├── dataset/                 # 训练数据集，需包含 data.yaml
├── onnx_model/              # YOLO 导出的 ONNX 输出目录
├── goke_model/              # Goke 转换后的 xmm 输出目录
├── train/train.py           # 训练脚本
├── ultralytics/export.py    # 导出脚本
└── opensource_model_zoo/    # Goke 转换依赖目录
```

## 镜像说明

### 1. yolov8 镜像

`docker/yolov8/Dockerfile` 当前基于：

- `ubuntu:20.04`
- Miniconda
- `torch==2.9.0`
- `torchvision==0.24.0`
- `torchaudio==2.9.0`
- `ultralytics`

构建命令：

```bash
cd docker/yolov8
docker build -t yolov8_image .
```

### 2. goke7605 镜像

`docker-compose.yml` 当前直接使用镜像：

```text
ubuntu18.04:goke7605
```

也就是说，启动 Compose 前，需要确保本地已经存在该镜像。

如果你需要自己构建工具链镜像，可参考：

- `docker/export/Dockerfile`
- `docker/export/Dockerfile.txt`
- `docker/export/README.txt`

## 启动服务

在确认本地已有以下镜像后启动：

- `yolov8_image`
- `ubuntu18.04:goke7605`

启动命令：

```bash
cd docker
docker-compose up -d
```

停止服务：

```bash
docker-compose down
```

查看状态：

```bash
docker-compose ps
```

查看日志：

```bash
docker logs -f yolov8
docker logs -f goke7605
```

## 服务行为说明

### yolov8 服务

启动命令来自 `docker-compose.yml`：

```yaml
command: bash /share/yolov8_run.sh
```

脚本逻辑见 `yolov8_run.sh`：

- 监听 `/share/dataset`
- 当检测到 `*.yaml` 文件写入或移动完成时触发训练
- 调用：

```bash
python /share/train/train.py \
    --data /share/dataset/data.yaml \
    --project /share/onnx_model \
    --name latest \
    --epochs 50 \
    --batch 32
```

- 训练完成后调用：

```bash
python /share/ultralytics/export.py \
    --model /share/onnx_model/latest/weights/best.pt \
    --format onnx \
    --imgsz 360 640
```

### goke7605 服务

启动命令来自 `docker-compose.yml`：

```yaml
command: bash /share/goke_run.sh
```

脚本逻辑见 `goke_run.sh`：

- 监听 `/share/onnx_model`
- 检测到新的 `.onnx` 文件后，根据文件名匹配任务目录
- 默认依赖：

```text
/share/opensource_model_zoo
```

- 执行 `python build.py`
- 生成的 `.xmm` 文件移动到：

```text
/share/goke_model
```

## 数据与输出目录

| 目录 | 说明 |
|------|------|
| `/share/dataset` | 训练数据集目录，需包含 `data.yaml` |
| `/share/onnx_model` | YOLOv8 导出的 ONNX 模型目录 |
| `/share/goke_model` | Goke 转换后的 `.xmm` 输出目录 |
| `/share/opensource_model_zoo` | 模型转换依赖目录 |

## 自定义训练

如需调整训练参数，编辑 `docker/yolov8_run.sh` 中这一段：

```bash
python /share/train/train.py \
    --data /share/dataset/data.yaml \
    --project /share/onnx_model \
    --name latest \
    --epochs 50 \
    --batch 32
```

如需调整导出参数，编辑：

```bash
python /share/ultralytics/export.py \
    --model /share/onnx_model/latest/weights/best.pt \
    --format onnx \
    --imgsz 360 640
```

## 常用命令

```bash
# 构建 yolov8 镜像
docker build -t yolov8_image docker/yolov8

# 启动服务
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker logs -f yolov8
docker logs -f goke7605

# 进入容器
docker exec -it yolov8 bash
docker exec -it goke7605 bash

# 停止服务
docker-compose -f docker/docker-compose.yml down
```

## 注意事项

1. `docker-compose.yml` 当前使用的是固定镜像名，不会自动构建镜像。
2. `yolov8` 服务依赖 NVIDIA 运行时，Compose 中已配置 `runtime: nvidia`。
3. 两个服务都依赖宿主机挂载目录 `/workdir/share:/share`。
4. `goke7605` 服务依赖 `/share/opensource_model_zoo` 内已有对应模型目录和 `build.py`。
5. `goke7605` 服务的输出目录实际为 `/share/goke_model`，不是 `/share/xmm_model`。

## 许可证

本项目仅供学习和内部使用。
