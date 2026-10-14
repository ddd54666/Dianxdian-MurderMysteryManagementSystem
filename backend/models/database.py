"""数据库连接管理、初始化建表、版本迁移。"""

import sqlite3
from datetime import datetime
from flask import g, current_app
from backend.config import get_db_path


def get_db():
    """获取当前请求的数据库连接（线程级 g 对象缓存）。"""
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db


def close_db(exception=None):
    """关闭请求的数据库连接。"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """首次运行时创建所有表和索引（CREATE TABLE IF NOT EXISTS）。"""
    db = get_db()
    db.executescript(_DDL_SCRIPT)


def migrate_db():
    """基于 db_version 表执行增量迁移（预留扩展入口）。"""
    db = get_db()
    cur = db.execute("SELECT MAX(version) FROM db_version")
    row = cur.fetchone()
    current = row[0] if row and row[0] else 0
    latest = _LATEST_DB_VERSION
    if current < latest:
        for ver in range(current + 1, latest + 1):
            _run_migration(db, ver)
        db.execute("UPDATE db_version SET version = ?", (latest,))
        db.commit()


def _run_migration(db, target_version):
    """执行单个版本的迁移 SQL（检查列是否已存在再执行）。"""
    migrations = _MIGRATIONS.get(target_version)
    if not migrations:
        return
    for sql in migrations:
        # ALTER TABLE ADD COLUMN 场景：先检查列是否已存在
        if sql.strip().upper().startswith('ALTER TABLE') and 'ADD COLUMN' in sql.upper():
            parts = sql.split()
            try:
                col_idx = parts.index('COLUMN') + 1
            except ValueError:
                col_idx = len(parts) - 1
            col_name = parts[col_idx]
            table_name = parts[2]
            exists = db.execute(f"PRAGMA table_info({table_name})").fetchall()
            if any(row[1] == col_name for row in exists):
                continue  # 列已存在，跳过
        db.execute(sql)


_LATEST_DB_VERSION = 1

_MIGRATIONS = {}

_DDL_SCRIPT = """
CREATE TABLE IF NOT EXISTS db_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scripts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL UNIQUE,
    type                TEXT    NOT NULL,
    category            TEXT    NOT NULL,
    unit_price          INTEGER NOT NULL,
    player_count        INTEGER NOT NULL,
    is_player_count_fixed INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL,
    CHECK(type IN ('欢乐','推理','恐怖','情感','机制')),
    CHECK(category IN ('盒装','城限')),
    CHECK(unit_price > 0),
    CHECK(player_count > 0)
);

CREATE TABLE IF NOT EXISTS dms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    notes       TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id       INTEGER NOT NULL,
    dm_count        INTEGER NOT NULL DEFAULT 1,
    unit_price      INTEGER NOT NULL,
    player_count    INTEGER NOT NULL,
    session_date    TEXT    NOT NULL,
    revenue         INTEGER NOT NULL,
    dm_salary       INTEGER NOT NULL DEFAULT 0,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE RESTRICT,
    CHECK(dm_count BETWEEN 1 AND 6),
    CHECK(unit_price > 0),
    CHECK(player_count > 0),
    CHECK(revenue >= 0),
    CHECK(dm_salary >= 0)
);

CREATE TABLE IF NOT EXISTS session_dms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL,
    dm_id       INTEGER NOT NULL,
    dm_salary   INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (dm_id)     REFERENCES dms(id) ON DELETE RESTRICT,
    UNIQUE(session_id, dm_id)
);

CREATE TABLE IF NOT EXISTS members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    gender      TEXT    NOT NULL,
    phone       TEXT    NOT NULL UNIQUE,
    balance     INTEGER NOT NULL DEFAULT 0,
    notes       TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL,
    CHECK(gender IN ('男','女')),
    CHECK(length(phone) = 11),
    CHECK(balance >= 0)
);

CREATE TABLE IF NOT EXISTS recharges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id       INTEGER NOT NULL,
    member_name     TEXT    NOT NULL,
    member_phone    TEXT    NOT NULL,
    recharge_time   TEXT    NOT NULL,
    pay_amount      INTEGER NOT NULL,
    bonus_amount    INTEGER NOT NULL DEFAULT 0,
    deleted_at      TEXT    DEFAULT NULL,
    created_at      TEXT    NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT,
    CHECK(pay_amount > 0),
    CHECK(bonus_amount >= 0)
);

CREATE TABLE IF NOT EXISTS consumptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id           INTEGER NOT NULL,
    member_name         TEXT    NOT NULL,
    member_phone        TEXT    NOT NULL,
    consumption_time    TEXT    NOT NULL,
    amount              INTEGER NOT NULL,
    script_name         TEXT    NOT NULL,
    deleted_at          TEXT    DEFAULT NULL,
    created_at          TEXT    NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT,
    CHECK(amount > 0)
);

CREATE TABLE IF NOT EXISTS carpools (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    carpool_date    TEXT    NOT NULL,
    script_id       INTEGER NOT NULL,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    author      TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scripts_type ON scripts(type);
CREATE INDEX IF NOT EXISTS idx_scripts_category ON scripts(category);
CREATE INDEX IF NOT EXISTS idx_dms_name ON dms(name);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_script ON sessions(script_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date_script ON sessions(session_date, script_id);
CREATE INDEX IF NOT EXISTS idx_session_dms_session ON session_dms(session_id);
CREATE INDEX IF NOT EXISTS idx_session_dms_dm ON session_dms(dm_id);
CREATE INDEX IF NOT EXISTS idx_members_name ON members(name);
CREATE INDEX IF NOT EXISTS idx_members_balance ON members(balance);
CREATE INDEX IF NOT EXISTS idx_recharges_member ON recharges(member_id);
CREATE INDEX IF NOT EXISTS idx_recharges_time ON recharges(recharge_time);
CREATE INDEX IF NOT EXISTS idx_consumptions_member ON consumptions(member_id);
CREATE INDEX IF NOT EXISTS idx_consumptions_time ON consumptions(consumption_time);
CREATE INDEX IF NOT EXISTS idx_carpools_date ON carpools(carpool_date);
CREATE INDEX IF NOT EXISTS idx_carpools_script ON carpools(script_id);
CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(created_at DESC);

INSERT INTO db_version (version) SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM db_version);
"""
