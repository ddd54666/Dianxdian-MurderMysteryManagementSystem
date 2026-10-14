"""拼车数据操作层。"""

from datetime import datetime
from backend.models.database import get_db


def _now_iso():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def list_carpools(page=1, page_size=20):
    """分页查询拼车列表，JOIN 剧本名称，计算是否过期。"""
    db = get_db()
    today = datetime.now().strftime('%Y-%m-%d')

    total = db.execute("SELECT COUNT(*) FROM carpools").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        "SELECT c.*, sc.name AS script_name, CASE WHEN c.carpool_date < ? THEN 1 ELSE 0 END AS is_expired "
        "FROM carpools c JOIN scripts sc ON c.script_id = sc.id "
        "ORDER BY c.carpool_date DESC LIMIT ? OFFSET ?",
        (today, page_size, offset)
    ).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item['is_expired'] = bool(item['is_expired'])
        result.append(item)

    return {'data': result, 'total': total, 'page': page, 'page_size': page_size}


def create_carpool(data, now=None):
    """新增拼车。"""
    if now is None:
        now = _now_iso()
    db = get_db()
    cur = db.execute(
        "INSERT INTO carpools (carpool_date, script_id, notes, created_at, updated_at) VALUES (?,?,?,?,?)",
        (data['carpool_date'], data['script_id'], data.get('notes', ''), now, now)
    )
    db.commit()
    return cur.lastrowid


def update_carpool(carpool_id, data, now=None):
    """编辑拼车。"""
    if now is None:
        now = _now_iso()
    db = get_db()
    db.execute(
        "UPDATE carpools SET carpool_date=?, script_id=?, notes=?, updated_at=? WHERE id=?",
        (data['carpool_date'], data['script_id'], data.get('notes', ''), now, carpool_id)
    )
    db.commit()


def delete_carpool(carpool_id):
    """删除拼车。"""
    db = get_db()
    db.execute("DELETE FROM carpools WHERE id = ?", (carpool_id,))
    db.commit()
