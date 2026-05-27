import json
import os

# ==========================
# 路径配置
# ==========================
json_dir = r"E:\pack\json"
txt_dir  = r"E:\pack\labels"

os.makedirs(txt_dir, exist_ok=True)

CLASS_ID = 0  # 类别

for file in os.listdir(json_dir):
    if not file.endswith(".json"):
        continue

    json_path = os.path.join(json_dir, file)
    txt_path = os.path.join(txt_dir, file.replace(".json", ".txt"))

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    W = data["imageWidth"]
    H = data["imageHeight"]
    shapes = data.get("shapes", [])

    lines = []

    for s in shapes:
        if s["shape_type"] != "rectangle":
            continue

        (x1, y1), (x2, y2) = s["points"]
        cx = (x1 + x2) / 2 / W
        cy = (y1 + y2) / 2 / H
        bw = abs(x2 - x1) / W
        bh = abs(y2 - y1) / H

        line = f"{CLASS_ID} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"
        lines.append(line)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✔ {file} -> {os.path.basename(txt_path)}")

print("\n✅ 全部转换完成（YOLO 矩形框格式）")