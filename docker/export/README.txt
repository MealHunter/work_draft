操作指南：
1. 加载工具链镜像前，先确定当前服务器的docker环境是否正常：
$ docker --version
-- docker版本建议在24.0.2及以上

2. 加载工具链镜像：
$ docker load -i ubuntu18.04_xmtvm_AI_TOOLCHAIN_V020_V3010_***.tar
-- 这里的 *** 指代镜像版本号

3. 创建及启动容器：
$ docker run -dit --name ### --net=host --shm-size 32G ubuntu18.04_xmtvm:AI_TOOLCHAIN_V020_V3010_***  /bin/bash
-- 这里的 ### 指代容器名字，自行命名，*** 指代镜像版本号

4. 将测试样例包opensource_model_zoo拷贝进容器中：
$ docker cp opensource_model_zoo.***.tar.gz ###:/root/xmedia/
-- 这里的 ### 指代第3步创建的容器名字

5. 进入容器：
$ docker exec -it ### bash
-- 这里的 ### 指代第3步创建的容器名字

6. 解压缩测试样例包：
$ cd root/xmedia
$ tar xf opensource_model_zoo.***.tar.gz

7. 样例测试：
$ cd opensource_model_zoo/object_detection/yolov5
$ python build_coco.py
等待测试完成即可。