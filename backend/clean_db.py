"""删除开发环境的数据库主文件，供测试环境重建空库。

使用方法：
    从项目根目录执行 python backend/clean_db.py，目标为项目根目录的 database.db。
    运行前必须停止后端及其他使用数据库的进程，并确认已有可用备份。
    删除无法撤销；正式经营数据不应使用此脚本清理。

行为说明：
    不需要额外第三方依赖，也不接受命令行参数。
    仅删除数据库主文件，不删除 config.json、backup/ 或数据库的 WAL、SHM 文件。
    脚本本身不重建表结构，之后启动后端时才会创建新的空库。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import get_db_path


def clean():
    """删除配置模块定位的数据库主文件；调用前需停止服务并保存备份。"""
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f'[OK] 已删除 {db_path}')
        print('     下次启动应用时将自动重建空数据库。')
    else:
        print(f'[!]  数据库文件不存在：{db_path}')


if __name__ == '__main__':
    clean()
