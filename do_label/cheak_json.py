import json
import os

# JSON 文件目录
json_dir = r"C:\Users\DELL\Desktop\mp4\fish\labels_json"
debug_file = r"C:\Users\DELL\Desktop\mp4\fish\debug_group_check.txt"

# 保存异常文件及对应的 group_id
abnormal_info = {}  # {file_name: [group_id,...]}

for file in os.listdir(json_dir):
    if not file.endswith(".json"):
        continue

    file_path = os.path.join(json_dir, file)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    shapes = data.get("shapes", [])

    # 收集每个 group_id 对应的 shapes
    group_shapes = {}
    for s in shapes:
        gid = s.get("group_id", None)
        if gid is None:
            continue
        group_shapes.setdefault(gid, []).append(s)

    # 检查每个 group_id
    for gid, items in group_shapes.items():
        rectangles = [s for s in items if s["shape_type"] == "rectangle"]
        heads = [s for s in items if s["shape_type"] == "point" and "head" in s["label"].lower()]
        tails = [s for s in items if s["shape_type"] == "point" and "tail" in s["label"].lower()]

        # 不允许一个 group_id 中出现两个 head 或两个 tail，或者没有 rectangle
        if len(rectangles) == 0 or len(heads) > 1 or len(tails) > 1:
            abnormal_info.setdefault(file, []).append(gid)

# 打印结果
if abnormal_info:
    print("以下 JSON 文件存在不符合 group_id 规则的情况：")
    for file, gids in sorted(abnormal_info.items()):
        print(f"{file}: group_id(s) -> {gids}")

    # 写入 debug 文件
    with open(debug_file, "w", encoding="utf-8") as f:
        for file, gids in sorted(abnormal_info.items()):
            f.write(f"{file}: group_id(s) -> {gids}\n")
    print(f"\n📝 debug 文件已保存：{debug_file}")
else:
    print("✅ 所有 JSON 文件的 group_id 都符合规则")
