import os
import random
import shutil

# 配置文件夹路径
image_dir = r'C:\Users\DELL\Desktop\mp4\fish\images'  # 图片文件夹
label_dir = r'C:\Users\DELL\Desktop\mp4\fish\labels'  # 标签文件夹
train_image_dir = r'C:\Users\DELL\Desktop\fish\train\images'  # 训练集图片存放路径
val_image_dir = r'C:\Users\DELL\Desktop\fish\val\images'  # 验证集图片存放路径
train_label_dir = r'C:\Users\DELL\Desktop\fish\train\labels'  # 训练集标签存放路径
val_label_dir = r'C:\Users\DELL\Desktop\fish\val\labels'  # 验证集标签存放路径

# 创建训练集和验证集文件夹
os.makedirs(train_image_dir, exist_ok=True)
os.makedirs(val_image_dir, exist_ok=True)
os.makedirs(train_label_dir, exist_ok=True)
os.makedirs(val_label_dir, exist_ok=True)

# 获取所有图片文件
image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]

# 打乱图片文件列表
random.shuffle(image_files)

# 按照8:2的比例划分训练集和验证集
split_index = int(0.8 * len(image_files))

train_images = image_files[:split_index]
val_images = image_files[split_index:]

# 将图片和标签移动到对应的文件夹
for image_file in train_images:
    label_file = image_file.replace('.jpg', '.txt').replace('.png', '.txt')
    
    # 移动图片
    shutil.move(os.path.join(image_dir, image_file), os.path.join(train_image_dir, image_file))
    
    # 移动标签
    if os.path.exists(os.path.join(label_dir, label_file)):
        shutil.move(os.path.join(label_dir, label_file), os.path.join(train_label_dir, label_file))

for image_file in val_images:
    label_file = image_file.replace('.jpg', '.txt').replace('.png', '.txt')
    
    # 移动图片
    shutil.move(os.path.join(image_dir, image_file), os.path.join(val_image_dir, image_file))
    
    # 移动标签
    if os.path.exists(os.path.join(label_dir, label_file)):
        shutil.move(os.path.join(label_dir, label_file), os.path.join(val_label_dir, label_file))

print("数据划分完成！")