import json
import os
import math

src_dir = r"C:\Users\DELL\Desktop\mp4\fish\labels_json_original"
dst_dir = r"C:\Users\DELL\Desktop\mp4\fish\labels_json"
debug_file = r"C:\Users\DELL\Desktop\mp4\fish\debug.txt"

os.makedirs(dst_dir, exist_ok=True)

def point_in_rect(px, py, rect):
    (x1, y1), (x2, y2) = rect
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    return xmin <= px <= xmax and ymin <= py <= ymax

def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

count = 0
debug_files = set()

for file in os.listdir(src_dir):
    if not file.endswith(".json"):
        continue

    count += 1
    print(f"\nprocessing: {file}")

    with open(os.path.join(src_dir, file), "r", encoding="utf-8") as f:
        data = json.load(f)

    shapes = data.get("shapes", [])
    rectangles = [s for s in shapes if s["shape_type"] == "rectangle"]

    # rectangle group_id
    for i, rect in enumerate(rectangles, start=1):
        rect["group_id"] = i

    # 每个 rectangle 内部 head/tail points
    rect_points = {r["group_id"]: {"head": [], "tail": []} for r in rectangles}

    # 收集每个 point 的候选 rectangle
    for s in shapes:
        if s["shape_type"] != "point":
            continue

        px, py = s["points"][0]
        s["group_id"] = None
        ptype = "head" if "head" in s["label"].lower() else "tail"

        candidate_gids = []
        for rect in rectangles:
            if point_in_rect(px, py, rect["points"]):
                candidate_gids.append(rect["group_id"])

        if not candidate_gids:
            print(f"[WARN] {file}: point '{s['label']}' not in any rectangle")
            continue

        # 如果 candidate_gids 只有一个，直接归属
        if len(candidate_gids) == 1:
            gid = candidate_gids[0]
        else:
            # 多框候选：选择距离已有对点最远的框
            max_d = -1
            gid = candidate_gids[0]
            for g in candidate_gids:
                pts_in_rect = rect_points[g]
                other_type_pts = pts_in_rect["tail"] if ptype == "head" else pts_in_rect["head"]
                if other_type_pts:
                    d = max(dist(s["points"][0], pt["points"][0]) for pt in other_type_pts)
                    if d > max_d:
                        max_d = d
                        gid = g
                else:
                    # 如果没有另一类型点，则也可以选择
                    gid = g
                    break

        # 分配 group_id 并加入 rect_points
        s["group_id"] = gid
        rect_points[gid][ptype].append(s)

        if len(rect_points[gid]["head"]) + len(rect_points[gid]["tail"]) > 2:
            debug_files.add(file)

    # 写入新目录
    with open(os.path.join(dst_dir, file), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 写 debug 文件
with open(debug_file, "w", encoding="utf-8") as f:
    for df in sorted(debug_files):
        f.write(df + "\n")

print(f"\n✅ 完成：共处理 {count} 个 json")
print(f"⚠️  出现异常点的文件数量：{len(debug_files)}")
print(f"📂 输出目录：{dst_dir}")
print(f"📝 debug 文件：{debug_file}")
