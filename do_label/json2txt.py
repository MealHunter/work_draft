import json
import os

# ==========================
# 路径配置
# ==========================
json_dir = r"C:\Users\DELL\Desktop\mp4\fish\labels_json"
txt_dir  = r"C:\Users\DELL\Desktop\mp4\fish\labels"

os.makedirs(txt_dir, exist_ok=True)

CLASS_ID = 0  # 鱼类别
KPT_ORDER = ["head", "tail"]  # 关键点顺序

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

    # group_id -> data
    groups = {}

    for s in shapes:
        gid = s.get("group_id")
        if gid is None:
            continue
        groups.setdefault(gid, {"rect": None, "kpts": {}})

        if s["shape_type"] == "rectangle":
            groups[gid]["rect"] = s

        elif s["shape_type"] == "point":
            label = s["label"].lower()
            if label in KPT_ORDER:
                groups[gid]["kpts"][label] = s["points"][0]

    lines = []

    for gid, g in groups.items():
        if g["rect"] is None:
            continue  # 没框直接跳过

        # ========== box ==========
        (x1, y1), (x2, y2) = g["rect"]["points"]
        cx = (x1 + x2) / 2 / W
        cy = (y1 + y2) / 2 / H
        bw = abs(x2 - x1) / W
        bh = abs(y2 - y1) / H

        line = [f"{CLASS_ID}", f"{cx:.6f}", f"{cy:.6f}", f"{bw:.6f}", f"{bh:.6f}"]

        # ========== keypoints ==========
        for kpt in KPT_ORDER:
            if kpt in g["kpts"]:
                x, y = g["kpts"][kpt]
                line.append(f"{x / W:.6f}")
                line.append(f"{y / H:.6f}")
            else:
                line.extend(["0", "0"])  # 缺失关键点

        lines.append(" ".join(line))

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✔ {file} -> {os.path.basename(txt_path)}")

print("\n✅ 全部转换完成（YOLOv8-Pose 格式）")
