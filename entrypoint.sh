#!/bin/bash

# 设置日志输出
echo "启动MetaGPT EazyTec客户端..."

# 执行Python脚本，使用uv运行
uv run eazytec_client.py

# 如果脚本异常退出，打印错误信息
if [ $? -ne 0 ]; then
    echo "错误：脚本执行失败"
    exit 1
fi 