#!/bin/sh

# 默认API地址，如果未提供
API_URL=${API_URL:-"http://127.0.0.1:3000"}
APP_PORT_1=${APP_PORT_1:-8001}

# 替换nginx配置中的环境变量
envsubst '$APP_PORT_1 $API_URL' < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp
mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf

# 替换前端应用中的环境配置文件(如果存在)
if [ -f /usr/share/nginx/html/env-config.js ]; then
  envsubst < /usr/share/nginx/html/env-config.js > /usr/share/nginx/html/env-config.js.tmp
  mv /usr/share/nginx/html/env-config.js.tmp /usr/share/nginx/html/env-config.js
fi

# 启动nginx
nginx -g "daemon off;" 