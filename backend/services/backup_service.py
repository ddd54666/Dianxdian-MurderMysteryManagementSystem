"""数据库备份服务：启动/关闭/周一/跨天自动备份，分目录清理旧备份。"""

import os
import shutil
import sqlite3
from datetime import date, datetime
from backend.config import get_db_path, get_daily_dir, get_weekly_dir, load_config


def _copy_db(dst_dir, filename):
    """WAL checkpoint 后复制 database.db 到指定目录，返回文件名或 None。"""
    src = get_db_path()
    if not os.path.exists(src):
        return None
    try:
        conn = sqlite3.connect(src)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except sqlite3.Error:
        pass
    dst = os.path.join(dst_dir, filename)
    shutil.copy2(src, dst)
    print(f"备份完成: {os.path.basename(dst)}")
    return filename


def backup_daily():
    """普通备份到 daily/ 目录，保留最近 backup_daily_keep 份。"""
    filename = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    if _copy_db(get_daily_dir(), filename):
        _cleanup(load_config().get('backup_daily_keep', 10), get_daily_dir())
        return filename
    return None


def backup_weekly():
    """周一备份到 weekly/ 目录，保留最近 backup_weekly_keep 份。"""
    filename = f'backup_weekly_{date.today().strftime("%Y%m%d")}.db'
    if _copy_db(get_weekly_dir(), filename):
        _cleanup(load_config().get('backup_weekly_keep', 5), get_weekly_dir())
        return filename
    return None


def maybe_backup():
    """统一备份入口：周一做 weekly 备份，否则距上次备份跨自然日时做 daily 备份。"""
    if is_monday():
        today = date.today().strftime('%Y%m%d')
        weekly_file = os.path.join(get_weekly_dir(), f'backup_weekly_{today}.db')
        if not os.path.exists(weekly_file):
            return backup_weekly()
    last = _last_backup_date()
    if last is None or last < date.today():
        return backup_daily()
    return None


def _last_backup_date():
    """返回最近一次备份的日期，无任何备份时返回 None。"""
    latest = ''
    for f in os.listdir(get_daily_dir()):
        if len(f) >= 15 and f.startswith('backup_') and f[7:15].isdigit():
            latest = max(latest, f[7:15])
    for f in os.listdir(get_weekly_dir()):
        if len(f) >= 22 and f.startswith('backup_weekly_') and f[14:22].isdigit():
            latest = max(latest, f[14:22])
    return date.fromisoformat(latest) if latest else None


def _cleanup(keep, subdir):
    """清理指定备份目录，按文件名排序保留最近 keep 份。"""
    files = sorted(f for f in os.listdir(subdir) if f.endswith('.db'))
    for fname in files[:-keep]:
        os.remove(os.path.join(subdir, fname))


def is_monday():
    """判断今天是否为周一。"""
    return date.today().weekday() == 0
