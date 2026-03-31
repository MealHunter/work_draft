import json
import os

# ==========================
# 路径配置
# ==========================
json_path = r"D:\yyb\dataset\images_640\anno.json"
txt_dir = r"D:\yyb\dataset\images_640\labels"

os.makedirs(txt_dir, exist_ok=True)

# 类别映射（可根据需要扩展）
class_map = {"fish": 0}

# 读取anno.json
with open(json_path, "r", encoding="utf-8") as f:
    annotations = json.load(f)

count = 0
for ann in annotations:
    filename = ann["filename"]
    # width = ann["width"]
    # height = ann["height"]
    data = ann.get("data", [])

    txt_filename = os.path.splitext(filename)[0] + ".txt"
    txt_path = os.path.join(txt_dir, txt_filename)

    lines = []
    for item in data:
        cls_name = item.get("class", "")
        position = item.get("position", "")

        if cls_name not in class_map:
            print(f"⚠ 未知类别: {cls_name}, 跳过")
            continue

        # position已经是归一化坐标 [x_center, y_center, width, height]
        # 格式: "[0.429167,0.451852,0.663542,0.641667]"
        pos_str = position.strip("[]")
        parts = [float(p.strip()) for p in pos_str.split(",")]

        if len(parts) != 4:
            print(f"⚠ {filename} 坐标格式错误: {position}")
            continue

        cx, cy, w, h = parts
        cls_id = class_map[cls_name]

        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    count += 1
    print(f"[OK] {filename} -> {txt_filename}")

print(f"\n[DONE] Converted {count} files")
