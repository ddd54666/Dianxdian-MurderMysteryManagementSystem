"""留言板数据操作层。"""

from datetime import datetime
from backend.models.database import get_db


def list_messages(page=1, page_size=20):
    """分页查询留言，按时间倒序。"""
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        "SELECT * FROM messages ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (page_size, offset)
    ).fetchall()

    return {'data': [dict(r) for r in rows], 'total': total, 'page': page, 'page_size': page_size}


def create_message(data, now=None):
    """新增留言。"""
    if now is None:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    db = get_db()
    cur = db.execute(
        "INSERT INTO messages (author, content, created_at) VALUES (?,?,?)",
        (data['author'], data['content'], now)
    )
    db.commit()
    return cur.lastrowid


def delete_message(message_id):
    """删除留言。"""
    db = get_db()
    db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    db.commit()
