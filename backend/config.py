"""为后端和维护脚本提供配置读写及运行时路径，不是独立命令行程序。

使用方法：
    调用 load_config() 获取配置字典，调用 save_config(cfg) 将修改写回 config.json。
    shop_name 控制店铺显示名称；修改后刷新前端即可读取新名称。
    secondary_password 在应用启动时加载，修改后需重启后端才能用于密码验证。
    服务端口、备份目录和保留份数的字段说明见 DEFAULT_CONFIG 与 README.md。

路径规则：
    开发环境以项目根目录为运行目录，打包后以可执行程序所在目录为运行目录。
    get_db_path() 返回该目录中的 database.db，与启动命令的当前工作目录无关。
    配置不存在时自动保存默认值；已有配置缺少字段时只在返回字典中补齐默认值。
    获取备份目录时会创建相应目录。配置包含明文密码，业务接口不得直接返回完整字典。
"""

import json
import os
import sys


def _get_base_dir():
    """获取运行目录，兼容 PyInstaller 打包和开发模式。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _get_base_dir()
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

DEFAULT_CONFIG = {
    'shop_name': '剧本杀店铺',
    'secondary_password': 'admin123',
    'port': 5000,
    'backup_dir': 'backup',
    'backup_daily_keep': 10,
    'backup_weekly_keep': 5
}


def load_config():
    """加载配置文件，不存在时用默认值生成。"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for key, val in DEFAULT_CONFIG.items():
            cfg.setdefault(key, val)
        return cfg
    cfg = dict(DEFAULT_CONFIG)
    save_config(cfg)
    return cfg


def save_config(cfg):
    """持久化配置到 config.json。"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_db_path():
    """获取数据库文件路径（与 exe 同级）。"""
    return os.path.join(BASE_DIR, 'database.db')


def get_backup_dir():
    """获取备份目录路径，不存在则自动创建。"""
    cfg = load_config()
    path = os.path.join(BASE_DIR, cfg['backup_dir'])
    os.makedirs(path, exist_ok=True)
    return path


def get_daily_dir():
    """获取每日备份目录路径，不存在则自动创建。"""
    path = os.path.join(get_backup_dir(), 'daily')
    os.makedirs(path, exist_ok=True)
    return path


def get_weekly_dir():
    """获取周一备份目录路径，不存在则自动创建。"""
    path = os.path.join(get_backup_dir(), 'weekly')
    os.makedirs(path, exist_ok=True)
    return path


def get_static_dir():
    """获取前端静态文件目录。打包后在 _internal 子目录中查找。"""
    frozen = getattr(sys, 'frozen', False)
    if frozen:
        base = os.path.dirname(sys.executable)
        path = os.path.join(base, '_internal', 'frontend', 'dist')
        if os.path.isdir(path):
            return path
    dev = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')
    return dev
