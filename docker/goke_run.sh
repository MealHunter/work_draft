#!/bin/bash

apt update && apt install -y inotify-tools

# 创建必要目录
mkdir -p /share/onnx_model /share/goke_model

TOOLCHAIN_DIR="/root/xmedia/opensource_model_zoo_v020"

echo "Waiting for new onnx model..."

inotifywait -m /share/onnx_model -e create |
while read path action file; do
    if [[ "$file" == *.onnx ]]; then
        # 等待文件写入完成
        sleep 2
        
        echo "Detected: $file"
        
        # 提取模型名称
        MODEL_NAME="${file%.onnx}"
        
        # 根据文件名判断任务类型和模型子目录
        case "$MODEL_NAME" in
            # Object Detection - yolov8 (精确匹配优先)
            yolov8n|yolov8s|yolov8m|yolov8l|yolov8x|yolov8-pose)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/yolov8"
                ;;
            # Object Detection - yolov5
            yolov5s_v7|yolov5s_v5|yolov5l|yolov5m|yolov5s|yolov5)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/yolov5"
                ;;
            # Object Detection - yolov9
            yolov9c|yolov9e|yolov9)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/yolov9"
                ;;
            # Object Detection - yolov10
            yolov10n|yolov10s|yolov10m|yolov10l|yolov10x)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/yolov10"
                ;;
            # Object Detection - yolov4
            yolov4m|yolov4e|yolov4tiny|yolov4)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/yolov4"
                ;;
            # Object Detection - yolov3
            yolov3-spp|yolov3tiny|yolov3)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/yolov3"
                ;;
            # Object Detection - nanodet
            nanodet_plus|nanodet_m|nanodet)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/nanodet"
                ;;
            # Object Detection - ppyoloe
            ppyoloe_l|ppyoloe_m|ppyoloe)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/ppyoloe"
                ;;
            # Object Detection - retinanet
            retinanet_l|retinanet_m|retinanet)
                TASK_DIR="$TOOLCHAIN_DIR/object_detection/retinanet"
                ;;
            # Classification
            resnet50_v2|resnet18|resnet50)
                TASK_DIR="$TOOLCHAIN_DIR/classification/$MODEL_NAME"
                ;;
            mobilenetv3|mobilenetv2|mobilenet)
                TASK_DIR="$TOOLCHAIN_DIR/classification/$MODEL_NAME"
                ;;
            squeezenet1_1|squeezenet1_0)
                TASK_DIR="$TOOLCHAIN_DIR/classification/squeezenet1_0"
                ;;
            inception_v3)
                TASK_DIR="$TOOLCHAIN_DIR/classification/inception_v3"
                ;;
            alexnet)
                TASK_DIR="$TOOLCHAIN_DIR/classification/alexnet"
                ;;
            shufflenet_v2)
                TASK_DIR="$TOOLCHAIN_DIR/classification/shufflenet_v2"
                ;;
            # Face Recognition
            face*)
                TASK_DIR="$TOOLCHAIN_DIR/face_recognize/mobilefacenet"
                ;;
            # Segmentation
            seg*|*_seg*)
                TASK_DIR="$TOOLCHAIN_DIR/segmentation(base)"
                ;;
            *)
                echo "Unknown model type: $file, skipping..."
                continue
                ;;
        esac
        
        echo "Using task dir: $TASK_DIR"
        
        if [ ! -d "$TASK_DIR" ]; then
            echo "Task dir not found: $TASK_DIR"
            continue
        fi
        
        if [ ! -f "$TASK_DIR/build.py" ]; then
            echo "build.py not found in: $TASK_DIR"
            continue
        fi
        
        cd "$TASK_DIR" || continue
        
        # 复制 onnx 模型到当前目录
        cp /share/onnx_model/"$file" ./ || { echo "Failed to copy model"; continue; }
        
        echo "Converting $file..."
        python build.py
        
        if [ $? -ne 0 ]; then
            echo "Conversion failed."
            rm -f ./"$file"
            continue
        fi
        
        # 移动输出的 xmm 模型到 goke_model
        mv ./*.xmm /share/goke_model/ 2>/dev/null || true
        mv ./*/*.xmm /share/goke_model/ 2>/dev/null || true
        
        # 清理 onnx 文件
        rm -f ./"$file"
        
        echo "Convert done."
    fi
done