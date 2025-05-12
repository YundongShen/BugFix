# Use a base image with Python3.9 and Nodejs20 slim version
FROM 47.103.57.78:30002/dokploy/python-nodejs:python3.11-nodejs22-slim-amd64

# Set npm and pip mirrors to Chinese sources
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

# 设置jemalloc环境变量，解决QEMU环境下的内存问题
ENV MALLOC_CONF="background_thread:false,narenas:2,tcache:false,metadata_thp:disabled"
ENV PYTHONMALLOC=malloc

# 设置pip相关环境变量
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=3

# Install Debian software needed by MetaGPT and clean up in one RUN command to reduce image size
RUN apt update &&\
    apt install -y libgomp1 git chromium fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 --no-install-recommends &&\
    apt clean && rm -rf /var/lib/apt/lists/*

# Install Mermaid CLI globally
ENV CHROME_BIN="/usr/bin/chromium" \
    puppeteer_config="/app/metagpt/config/puppeteer-config.json"\
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true" 
RUN npm install -g @mermaid-js/mermaid-cli -registry=https://registry.npmmirror.com --verbose &&\
    npm cache clean --force

# Install Python dependencies and install MetaGPT
COPY . /app/metagpt
WORKDIR /app/metagpt

# 安装uv包管理器（使用pip而不是curl）
RUN python -m pip install --upgrade pip --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple &&\
    pip install uv --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 创建Python 3.11虚拟环境并激活
RUN uv venv .venv --python=3.11
ENV PATH="/app/metagpt/.venv/bin:$PATH"

# 优化安装顺序，先安装基础依赖 - 分批安装以减少内存压力
RUN mkdir -p workspace &&\ 
    uv pip install --no-cache-dir -U pip setuptools wheel --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 分批安装依赖，减轻内存压力
RUN uv pip install --no-cache-dir numpy pandas pydantic --index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN uv pip install --no-cache-dir -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN uv pip install -e .  --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制并设置entrypoint.sh权限
COPY entrypoint.sh /app/metagpt/entrypoint.sh
RUN chmod +x /app/metagpt/entrypoint.sh

# 使用entrypoint.sh作为容器启动命令
CMD ["/app/metagpt/entrypoint.sh"]

