#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生产环境 WSGI 启动脚本（兼容 waitress / gunicorn / uwsgi）
因为 Python 包名不能以数字开头，所以在这里动态加载 app.py 并导出 Flask app。
用法：
  waitress-serve --host=0.0.0.0 --port=$PORT --threads=8 run_server:app
  gunicorn -w 2 -b 0.0.0.0:$PORT run_server:app
  python run_server.py  # 直接启动也可以
"""
import os
import sys
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

APP_PATH = os.path.join(PROJECT_ROOT, "4_application_layer", "web_app", "app.py")

_spec = importlib.util.spec_from_file_location("app_module", APP_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"无法加载 Flask 入口: {APP_PATH}")

_app_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_app_module)

# 导出 Flask 应用对象
app = _app_module.app

# 初始化系统（仅当直接 python run_server.py 时触发一次；waitress/gunicorn 也会执行到这里）
if hasattr(_app_module, "init_system"):
    _app_module.init_system()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    try:
        from waitress import serve
        print(f"[Prod] 使用 waitress 启动，端口 {port}，线程 8")
        serve(app, host="0.0.0.0", port=port, threads=8)
    except ImportError:
        print("[Dev] waitress 未安装，回退到 Flask 开发服务器")
        app.run(host="0.0.0.0", port=port, threaded=True)
