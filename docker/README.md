# YOLOv8 Docker 训练与部署项目

基于 Docker 的 YOLOv8 模型训练、自动导出及模型转换流水线项目。

## 项目概述

本项目实现了一个自动化机器学习流水线，包含以下两个核心服务：

1. **YOLOv8 训练服务** - 监听数据集变化，自动训练模型并导出 ONNX 格式
2. **Goke 转换服务** - 监听 ONNX 模型生成，自动转换为 xmm 格式

## 架构

```
┌─────────────────┐     ┌─────────────────┐
│   YOLOv8 容器   │     │   Goke 容器     │
│                 │     │                 │
│ - 数据集监控    │     │ - ONNX 模型监控 │
│ - 模型训练      │────▶│ - 模型转换      │
│ - ONNX 导出    │     │ - xmm 模型输出  │
└─────────────────┘     └─────────────────┘
         │                       │
         └──────────┬──────────────┘
                    │
              /share 共享目录
```

## 目录结构

```
docker/
├── docker-compose.yml      # Docker Compose 配置
├── yolov8/                 # YOLOv8 项目
│   ├── Dockerfile         # YOLOv8 容器镜像
│   └── ultralytics-8.3.57/# Ultralytics 库
│       ├── yolov8_train.py       # 训练脚本
│       ├── yolov8_train_pose.py # 姿态估计训练
│       ├── yolov8_train_fish.py # 鱼类检测训练
│       ├── yolov8_process.py    # 数据处理脚本
│       └── ...
├── yolov8_run.sh          # YOLOv8 容器启动脚本
└── goke_run.sh            # Goke 容器启动脚本
```

## 快速开始

### 前置要求

- Docker
- Docker Compose
- NVIDIA GPU (用于 YOLOv8 训练)
- NVIDIA Container Toolkit

### 构建镜像

```bash
# 构建 YOLOv8 镜像
cd docker/yolov8
docker build -t yolov8_image .

# 或者使用 Docker Compose 自动构建
cd docker
docker-compose build
```

### 启动服务

```bash
cd docker
docker-compose up -d
```

### 查看日志

```bash
# 查看 YOLOv8 服务日志
docker logs -f yolov8

# 查看 Goke 服务日志
docker logs -f goke
```

## 服务详情

### YOLOv8 训练服务

- **基础镜像**: `pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime`
- **功能**:
  - 监听 `/share/dataset` 目录变化
  - 检测到新数据后自动开始训练
  - 训练完成后自动导出 ONNX 模型
  - 输出模型保存到 `/share/onnx_model`
- **训练参数**:
  - Epochs: 50
  - Batch Size: 32
  - 图像尺寸: 640x352

### Goke 转换服务

- **功能**:
  - 监听 `/share/onnx_model` 目录
  - 检测到新的 `.onnx` 文件后自动转换
  - 使用 `convert_tool` 转换为 xmm 格式
  - 输出模型保存到 `/share/xmm_model`

## 数据目录

| 目录 | 描述 |
|------|------|
| `/share/dataset` | 训练数据集目录 |
| `/share/onnx_model` | ONNX 模型输出目录 |
| `/share/xmm_model` | xmm 模型输出目录 |

## 自定义训练

### 修改训练参数

编辑 `yolov8_run.sh` 文件：

```bash
python /app/ultralytics/train.py \
    --data /share/dataset/data.yaml \
    --project /share/onnx_model \
    --name latest \
    --epochs 100 \      # 修改 epoch 数
    --batch 16         # 修改 batch size
```

### 使用自定义数据集

1. 将数据集放入 `/share/dataset` 目录
2. 确保数据集配置文件 `data.yaml` 存在
3. 服务会自动检测到变化并开始训练

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart yolov8

# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f
```

## 依赖

- Python 3.8+
- PyTorch 2.2.0
- Ultralytics YOLOv8
- CUDA 12.1
- cuDNN 8

## 注意事项

1. 确保主机已安装 NVIDIA 驱动和 Docker NVIDIA 运行时
2. 共享目录 `/share` 需要在主机上预先创建并具有正确权限
3. Goke 服务的 `convert_tool` 需要自行准备

## 许可证

本项目仅供学习和内部使用。
