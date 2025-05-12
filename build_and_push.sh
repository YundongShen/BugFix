#!/bin/bash

# 定义变量
REGISTRY="47.103.57.78:30002"
NAMESPACE="dokploy"
IMAGE_NAME="metagpt"
TAG=$(date +"%Y%m%d%H%M%S")
PLATFORM="linux/amd64"  # 指定目标平台为 linux/amd64

# 显示构建信息
echo "====================================="
echo "开始构建 ${IMAGE_NAME} 镜像"
echo "镜像标签: ${TAG}"
echo "目标平台: ${PLATFORM}"
echo "====================================="

# 构建Docker镜像，添加平台参数、详细输出和超时设置
echo "开始构建镜像，详细模式..."
docker build --progress=plain  \
  -t ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG} .

# 检查构建是否成功
if [ $? -eq 0 ]; then
    echo "镜像构建成功: ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}"
    
    # 添加latest标签
    docker tag ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG} ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest
    
    # 推送镜像到仓库
    echo "正在推送镜像到 ${REGISTRY}..."
    docker push ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}
    docker push ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest
    
    if [ $? -eq 0 ]; then
        echo "====================================="
        echo "镜像推送成功！"
        echo "镜像: ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}"
        echo "镜像: ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest"
        echo "平台: ${PLATFORM}"
        echo "====================================="
    else
        echo "镜像推送失败，请检查网络或仓库权限。"
        exit 1
    fi
else
    echo "镜像构建失败，请检查Dockerfile和构建环境。"
    echo "请查看构建日志以获取更多信息。"
    exit 1
fi 