# Render / Railway / Heroku 生产启动命令
# waitress 是跨平台生产级 WSGI 服务器（无需编译依赖，纯 Python）
web: waitress-serve --host=0.0.0.0 --port=$PORT --threads=8 run_server:app
