"""Flask 应用工厂与入口。"""

import os
import sys

# 确保项目根目录在 Python 路径中
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import atexit
import threading
import time
import webbrowser
from flask import Flask, send_from_directory, request, jsonify
from backend.config import load_config, get_static_dir
from backend.models.database import init_db, migrate_db, close_db, get_db
from backend.services.backup_service import maybe_backup


def _startup_backup():
    """系统启动时自动备份，输出备份结果或跳过原因。"""
    try:
        if maybe_backup() is None:
            print("今日已有备份，启动时跳过自动备份")
    except Exception as e:
        print(f"启动备份失败: {e}")


def _exit_backup():
    """系统关闭时自动备份。"""
    try:
        maybe_backup()
    except Exception as e:
        print(f"退出备份失败: {e}")


def _scheduled_backup_loop():
    """后台守护线程，每小时检查一次跨天自动备份。"""
    while True:
        time.sleep(3600)
        try:
            maybe_backup()
        except Exception as e:
            print(f"定时备份失败: {e}")


def create_app():
    """创建并配置 Flask 应用。"""
    app = Flask(__name__, static_folder=None)

    cfg = load_config()
    app.config['SECONDARY_PASSWORD'] = cfg['secondary_password']

    with app.app_context():
        init_db()
        migrate_db()

    _startup_backup()
    atexit.register(_exit_backup)
    threading.Thread(target=_scheduled_backup_loop, daemon=True).start()

    app.teardown_appcontext(close_db)

    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_static(app)

    app.add_url_rule('/api/system/health', 'health', lambda: jsonify({'status': 'ok'}))

    return app


def _register_blueprints(app):
    """注册所有路由蓝图。"""
    from backend.routes.scripts import bp as scripts_bp
    from backend.routes.dms import bp as dms_bp
    from backend.routes.sessions import bp as sessions_bp
    from backend.routes.members import bp as members_bp
    from backend.routes.carpools import bp as carpools_bp
    from backend.routes.messages import bp as messages_bp
    from backend.routes.stats import bp as stats_bp
    from backend.routes.auth import bp as auth_bp
    from backend.routes.system import bp as system_bp

    app.register_blueprint(scripts_bp)
    app.register_blueprint(dms_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(carpools_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(system_bp)


def _register_error_handlers(app):
    """全局错误处理。"""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': str(e.description) if e.description else '请求参数错误'}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': '资源不存在'}), 404

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({'error': str(e.description) if e.description else '操作冲突'}), 409

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': '服务器内部错误'}), 500


def _configure_static(app):
    """配置静态文件服务：开发时无操作（Vite 代理），打包后 serve dist 文件。"""
    static_dir = get_static_dir()

    if not os.path.isdir(static_dir):
        return

    @app.route('/')
    def index():
        return send_from_directory(static_dir, 'index.html')

    @app.route('/assets/<path:filename>')
    def static_assets(filename):
        return send_from_directory(os.path.join(static_dir, 'assets'), filename)

    @app.route('/<path:filename>')
    def static_fallback(filename):
        path = os.path.join(static_dir, filename)
        if os.path.isfile(path):
            return send_from_directory(static_dir, filename)
        return send_from_directory(static_dir, 'index.html')


if __name__ == '__main__':
    app = create_app()
    cfg = load_config()
    port = cfg.get('port', 5000)

    frozen = getattr(sys, 'frozen', False)
    # 打包后自动打开浏览器，开发模式下由外部脚本控制
    if frozen:
        threading.Timer(2.0, lambda: webbrowser.open(f'http://localhost:{port}')).start()

    print(f"Dianxdian_Manage 服务启动: http://localhost:{port}")
    print(f"打包模式: {'是' if frozen else '否（开发模式）'}")
    app.run(host='127.0.0.1', port=port, debug=not frozen)
