# 使用 Ubuntu 18.04 作为基础镜像
FROM ubuntu:18.04

# 设置环境变量, 避免安装过程中出现交互提示
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
RUN mkdir -p /root/xmedia
WORKDIR /root/xmedia

# 备份原有的源列表
RUN cp /etc/apt/sources.list /etc/apt/sources.list.bak

# 更新源
RUN sed -i 's/archive.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN cat /etc/apt/sources.list
RUN apt-get clean
RUN apt-get -y update --fix-missing -o Acquire-by-hash=yes -o Acquire::https::No-Cache=True -o Acquire::http::No-Cache=True

# 更新系统软件包列表并安装必要的依赖
RUN apt-get install --fix-missing -y wget
RUN apt-get install -y build-essential
RUN apt-get install -y libgl1-mesa-glx
RUN apt-get install -y libglib2.0-0
RUN apt-get install -y vim
RUN apt-get install -y git
RUN apt-get install -y zip
RUN apt-get install -y unzip
RUN apt-get install -y inotify-tools
RUN apt-get install --fix-missing -y llvm-8
RUN apt-get install --fix-missing -y clang-8

# 清理工作
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# 验证安装
RUN llvm-config-8 --version
RUN clang-8 --version

# 清理工作
RUN rm -rf /tmp/*

# 下载 cmake 3.18.0 安装包
RUN wget -P /tmp/ https://cmake.org/files/v3.18/cmake-3.18.0-Linux-x86_64.sh

# 安装 CMake 3.18.0
RUN chmod +x /tmp/cmake-3.18.0-Linux-x86_64.sh \
    && /tmp/cmake-3.18.0-Linux-x86_64.sh --prefix=/usr/local --skip-license \
    && rm -rf /tmp/*

# 下载 miniconda3 py38 23.11.0-2 安装包
RUN wget -P /tmp/ https://repo.anaconda.com/miniconda/Miniconda3-py38_23.11.0-2-Linux-x86_64.sh

# 安装 Miniconda3 py38 23.11.0-2
RUN chmod +x /tmp/Miniconda3-py38_23.11.0-2-Linux-x86_64.sh \
    && bash /tmp/Miniconda3-py38_23.11.0-2-Linux-x86_64.sh -b \
    && rm -rf /tmp/*

# 设置 Miniconda3 环境变量
ENV PATH="/root/miniconda3/bin:${PATH}"
ENV CONDA_HOME="/root/miniconda3"
ENV LD_LIBRARY_PATH="${CONDA_HOME}/lib"
ENV LD_LIBRARY_PATH="${CONDA_HOME}/lib:${LD_LIBRARY_PATH}"

# 初始化 conda 并设置自动激活 base 环境
RUN /root/miniconda3/bin/conda init bash \
    && echo "conda activate base" >> ~/.bashrc

# 清理工作
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 验证安装
RUN cmake --version
RUN conda --version

# 安装 xmtvm 工具链环境
COPY AI_TOOLCHAIN_V020_V3010_*.tar.gz /tmp/AI_TOOLCHAIN_V020_V3010.tar.gz
RUN tar xf /tmp/AI_TOOLCHAIN_V020_V3010.tar.gz -C /tmp/
RUN chmod +x /tmp/install.sh && /tmp/install.sh \
    && rm -rf /tmp/*

# 验证安装
RUN xmtvmc --version
RUN mqbench --version
RUN onnx2torch --version

# 复制整个项目目录
COPY opensource_model_zoo.v020.tar.gz /xmedia/

RUN cd /xmedia && tar xf opensource_model_zoo.v020.tar.gz && rm -rf opensource_model_zoo.v020.tar.gz

WORKDIR /xmedia

# 默认命令
CMD ["bash"]

