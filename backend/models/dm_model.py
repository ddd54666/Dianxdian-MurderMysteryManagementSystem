"""DM数据操作层。"""

from datetime import datetime
from backend.models.database import get_db
from backend.models.script_model import ConflictError


def list_dms(search=None, page=1, page_size=20):
    """分页查询DM列表，默认按本月开本次数降序。"""
    db = get_db()
    now = datetime.now()
    this_month = now.strftime('%Y-%m')

    base = ("FROM dms LEFT JOIN session_dms sd ON dms.id = sd.dm_id "
            "LEFT JOIN sessions s ON sd.session_id = s.id AND s.session_date LIKE ?")

    params = [f"{this_month}%"]

    if search:
        base += " WHERE dms.name LIKE ?"
        params.append(f"%{search}%")

    total = db.execute(f"SELECT COUNT(DISTINCT dms.id) {base}", params).fetchone()[0]

    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT dms.*, COUNT(s.id) AS session_count_this_month {base} "
        "GROUP BY dms.id ORDER BY session_count_this_month DESC, dms.name LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()

    return {'data': [dict(r) for r in rows], 'total': total, 'page': page, 'page_size': page_size}


def search_dms(q, limit=10):
    """模糊搜索DM姓名（自动补全用）。"""
    db = get_db()
    rows = db.execute(
        "SELECT id, name FROM dms WHERE name LIKE ? ORDER BY name LIMIT ?",
        (f"%{q}%", limit)
    ).fetchall()
    return [dict(r) for r in rows]


def get_dm_by_id(dm_id):
    """按ID获取单个DM。"""
    db = get_db()
    return db.execute("SELECT * FROM dms WHERE id = ?", (dm_id,)).fetchone()


def create_dm(data, now=None):
    """新增DM。"""
    if now is None:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    db = get_db()
    cur = db.execute(
        "INSERT INTO dms (name, notes, created_at) VALUES (?,?,?)",
        (data['name'], data.get('notes', ''), now)
    )
    db.commit()
    return cur.lastrowid


def update_dm(dm_id, data):
    """编辑DM信息。"""
    db = get_db()
    db.execute(
        "UPDATE dms SET name=?, notes=? WHERE id=?",
        (data['name'], data.get('notes', ''), dm_id)
    )
    db.commit()


def delete_dm(dm_id):
    """删除DM，有关联场次则禁止。"""
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM session_dms WHERE dm_id = ?", (dm_id,)).fetchone()[0]
    if count > 0:
        raise ConflictError('该DM有关联场次，无法删除')
    db.execute("DELETE FROM dms WHERE id = ?", (dm_id,))
    db.commit()


def get_dm_sessions(dm_id, page=1, page_size=20):
    """查询DM的开本历史。"""
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM session_dms sd JOIN sessions s ON sd.session_id = s.id WHERE sd.dm_id = ?",
        (dm_id,)
    ).fetchone()[0]

    offset = (page - 1) * page_size
    rows = db.execute(
        "SELECT s.id AS session_id, s.session_date, sc.name AS script_name, "
        "s.dm_count, sd.dm_salary "
        "FROM session_dms sd "
        "JOIN sessions s ON sd.session_id = s.id "
        "JOIN scripts sc ON s.script_id = sc.id "
        "WHERE sd.dm_id = ? ORDER BY s.session_date DESC LIMIT ? OFFSET ?",
        (dm_id, page_size, offset)
    ).fetchall()

    return {
        'data': [dict(r) for r in rows],
        'total': total, 'page': page, 'page_size': page_size
    }
