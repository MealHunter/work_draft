FROM ubuntu18.04_xmtvm:AI_TOOLCHAIN_V020_V3010_145_20250827

WORKDIR /xmedia


# 复制整个项目目录
COPY opensource_model_zoo.v020.tar.gz /xmedia

RUN tar xf opensource_model_zoo.v020.tar.gz

WORKDIR /xmedia

# 默认命令
CMD ["bash"]
