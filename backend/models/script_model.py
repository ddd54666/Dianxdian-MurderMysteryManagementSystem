"""剧本数据操作层。"""

from datetime import datetime
from backend.models.database import get_db


def list_scripts(search=None, type=None, category=None, page=1, page_size=20):
    """分页查询剧本列表，支持名称搜索和类型/种类筛选。"""
    db = get_db()
    conditions, params = [], []

    if search:
        conditions.append("name LIKE ?")
        params.append(f"%{search}%")
    if type:
        conditions.append("type = ?")
        params.append(type)
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = db.execute(f"SELECT COUNT(*) FROM scripts {where}", params).fetchone()[0]

    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT * FROM scripts {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()

    return {'data': [dict(r) for r in rows], 'total': total, 'page': page, 'page_size': page_size}


def search_scripts(q, limit=10):
    """模糊搜索剧本名称（自动补全用）。"""
    db = get_db()
    rows = db.execute(
        "SELECT id, name, type, category, unit_price, player_count, is_player_count_fixed "
        "FROM scripts WHERE name LIKE ? ORDER BY name LIMIT ?",
        (f"%{q}%", limit)
    ).fetchall()
    return [dict(r) for r in rows]


def get_script_by_id(script_id):
    """按ID获取单个剧本。"""
    db = get_db()
    return db.execute("SELECT * FROM scripts WHERE id = ?", (script_id,)).fetchone()


def create_script(data, now=None):
    """新增剧本，名称重复返回 409 错误。"""
    if now is None:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    db = get_db()
    existing = db.execute("SELECT id FROM scripts WHERE name = ?", (data['name'],)).fetchone()
    if existing:
        raise ConflictError('剧本名称已存在')

    cur = db.execute(
        "INSERT INTO scripts (name, type, category, unit_price, player_count, is_player_count_fixed, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (data['name'], data['type'], data['category'], data['unit_price'],
         data['player_count'], 1 if data.get('is_player_count_fixed') else 0, now, now)
    )
    db.commit()
    return cur.lastrowid


def update_script(script_id, data, now=None):
    """编辑剧本信息。"""
    if now is None:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    db = get_db()
    existing = db.execute("SELECT name FROM scripts WHERE name = ? AND id != ?",
                          (data['name'], script_id)).fetchone()
    if existing:
        raise ConflictError('剧本名称已存在')

    db.execute(
        "UPDATE scripts SET name=?, type=?, category=?, unit_price=?, player_count=?, "
        "is_player_count_fixed=?, updated_at=? WHERE id=?",
        (data['name'], data['type'], data['category'], data['unit_price'],
         data['player_count'], 1 if data.get('is_player_count_fixed') else 0, now, script_id)
    )
    db.commit()


def delete_script(script_id):
    """删除剧本，有关联场次或拼车则禁止。"""
    db = get_db()
    sess = db.execute("SELECT COUNT(*) FROM sessions WHERE script_id = ?", (script_id,)).fetchone()[0]
    if sess > 0:
        raise ConflictError('该剧本有关联场次，无法删除')
    carp = db.execute("SELECT COUNT(*) FROM carpools WHERE script_id = ?", (script_id,)).fetchone()[0]
    if carp > 0:
        raise ConflictError('该剧本有关联拼车，无法删除')

    db.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
    db.commit()


class ConflictError(Exception):
    """业务冲突异常（409）。"""
    pass
