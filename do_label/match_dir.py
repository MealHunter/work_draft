"""
两个文件夹文件名匹配同步脚本
按文件名（去扩展名）匹配，将文件夹A中与文件夹B不匹配的文件移动到unmatched目录
"""

import os
import shutil


# 配置路径
dir_a = r"E:\pack\dataset\label"        # 文件夹A（要同步的文件夹）
dir_b = r"E:\pack\dataset\img"        # 文件夹B（参考文件夹）
unmatched_dir = r"E:\pack\dataset\move"  # 不匹配文件移入的目录


def get_stem_set(folder):
    """获取文件夹中所有文件的去扩展名集合"""
    return {os.path.splitext(f)[0] for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))}


def main():
    if not os.path.exists(dir_a):
        print(f"文件夹A不存在: {dir_a}")
        return
    if not os.path.exists(dir_b):
        print(f"文件夹B不存在: {dir_b}")
        return

    os.makedirs(unmatched_dir, exist_ok=True)

    stems_a = get_stem_set(dir_a)
    stems_b = get_stem_set(dir_b)

    matched = stems_a & stems_b
    only_a = stems_a - stems_b
    only_b = stems_b - stems_a

    print(f"文件夹A文件数: {len(stems_a)}")
    print(f"文件夹B文件数: {len(stems_b)}")
    print(f"匹配文件数: {len(matched)}")
    print(f"仅A有: {len(only_a)}")
    print(f"仅B有: {len(only_b)}")

    if only_b:
        print(f"\n【仅文件夹B存在的文件名】({len(only_b)}个):")
        for name in sorted(only_b)[:20]:
            print(f"  {name}")
        if len(only_b) > 20:
            print(f"  ... 还有{len(only_b) - 20}个")

    # 移动文件夹A中不匹配的文件
    if not only_a:
        print("\n文件夹A中无不匹配的文件")
        return

    moved = 0
    for fname in os.listdir(dir_a):
        fpath = os.path.join(dir_a, fname)
        if not os.path.isfile(fpath):
            continue
        stem = os.path.splitext(fname)[0]
        if stem in only_a:
            shutil.move(fpath, os.path.join(unmatched_dir, fname))
            print(f"已移动(不匹配): {fname}")
            moved += 1

    print(f"\n完成！移动 {moved} 个不匹配文件到 {unmatched_dir}")


if __name__ == "__main__":
    main()