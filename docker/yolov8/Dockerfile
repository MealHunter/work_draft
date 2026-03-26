# =========================
# 1) 基础镜像
# =========================
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# =========================
# 2) 系统依赖
# =========================
RUN apt update && apt install -y \
	wget \
	curl \
	gnupg \
	lsb-release \
    inotify-tools \
	git \
	unzip \
    libgl1 \
    libglib2.0-0 \
    vim \
	&& rm -rf /var/lib/apt/lists/*
 

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh \
	&& bash miniconda.sh -b -p /root/miniconda3 \
	&& rm miniconda.sh

# 配置 conda PATH（Docker 正确方式）
ENV PATH=/root/miniconda3/bin:$PATH

# 初始化conda
RUN conda init bash

# =========================
# 6) 进入容器默认工作目录
# =========================
WORKDIR /root/workdir

#==========================
# 验证安装
#==========================
RUN conda --version



# =========================
# 7) 基于base创建yolov8运行环境
# =========================
RUN pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu130

RUN pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple

CMD ["/bin/bash"]
