#!/bin/bash

# 检查 data.yaml 是否存在
if [ ! -f /share/dataset/data.yaml ]; then
    echo "Warning: data.yaml not found in /share/dataset, waiting..."
    sleep 30
fi

echo "Waiting for dataset update..."

inotifywait -m /share/dataset -e moved_to -e close_write |
while read path action file; do
    # 只处理 yaml 文件变化
    if [[ "$file" == *.yaml ]]; then
        echo "Dataset changed: $file, start training..."
        
        # 训练
        python /share/train/train.py \
            --data /share/dataset/data.yaml \
            --project /share/onnx_model \
            --name latest \
            --epochs 50 \
            --batch 32
        
        # 检查训练是否成功
        if [ $? -ne 0 ]; then
            echo "Training failed, skipping export."
            continue
        fi
        
        # 导出
        python /share/ultralytics/export.py \
            --model /share/onnx_model/latest/weights/best.pt \
            --format onnx \
            --imgsz 360 640
        
        if [ $? -eq 0 ]; then
            echo "Training and export finished."
        else
            echo "Export failed."
        fi
    fi
done