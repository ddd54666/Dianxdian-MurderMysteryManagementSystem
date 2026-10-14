"""场次数据操作层。"""

from datetime import datetime
from backend.models.database import get_db
from backend.models.script_model import ConflictError


def list_sessions(year=None, month=None, type=None, dm_id=None, script_id=None, page=1, page_size=20):
    """分页查询场次列表，JOIN 剧本和DM信息。"""
    db = get_db()
    conditions, params = [], []

    if year and month:
        conditions.append("s.session_date LIKE ?")
        params.append(f"{year}-{month:02d}%")
    elif year:
        conditions.append("s.session_date LIKE ?")
        params.append(f"{year}-%")

    if type:
        conditions.append("sc.type = ?")
        params.append(type)
    if script_id:
        conditions.append("s.script_id = ?")
        params.append(script_id)
    if dm_id:
        conditions.append("s.id IN (SELECT session_id FROM session_dms WHERE dm_id = ?)")
        params.append(dm_id)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = db.execute(
        f"SELECT COUNT(*) FROM sessions s JOIN scripts sc ON s.script_id = sc.id {where}", params
    ).fetchone()[0]

    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT s.*, sc.name AS script_name, sc.type AS script_type, sc.category AS script_category "
        f"FROM sessions s JOIN scripts sc ON s.script_id = sc.id "
        f"{where} ORDER BY s.session_date DESC, s.id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item['dms'] = _get_session_dms(db, r['id'])
        result.append(item)

    return {'data': result, 'total': total, 'page': page, 'page_size': page_size}


def get_session(session_id):
    """获取场次详情（含DM列表）。"""
    db = get_db()
    row = db.execute(
        "SELECT s.*, sc.name AS script_name, sc.type AS script_type, sc.category AS script_category "
        "FROM sessions s JOIN scripts sc ON s.script_id = sc.id WHERE s.id = ?",
        (session_id,)
    ).fetchone()
    if not row:
        return None
    item = dict(row)
    item['dms'] = _get_session_dms(db, session_id)
    return item


def _get_session_dms(db, session_id):
    """查询场次关联的DM列表（含每DM薪资）。"""
    dm_rows = db.execute(
        "SELECT d.id, d.name, sd.dm_salary FROM session_dms sd JOIN dms d ON sd.dm_id = d.id WHERE sd.session_id = ?",
        (session_id,)
    ).fetchall()
    return [dict(r) for r in dm_rows]


def create_session(data, now=None):
    """新增场次（事务：INSERT sessions + session_dms，支持每DM薪资）。"""
    if now is None:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    db = get_db()

    script = db.execute("SELECT id FROM scripts WHERE id = ?", (data['script_id'],)).fetchone()
    if not script:
        raise ConflictError('剧本不存在')

    dm_ids = data['dm_ids']
    if len(dm_ids) != data['dm_count']:
        raise ConflictError('DM人数与DM列表数量不匹配')

    for dm_id in dm_ids:
        dm = db.execute("SELECT id FROM dms WHERE id = ?", (dm_id,)).fetchone()
        if not dm:
            raise ConflictError(f'DM(ID={dm_id})不存在')

    # 每DM薪资：取 dm_salaries 数组，不够的补0
    dm_salaries = data.get('dm_salaries', []) or []
    while len(dm_salaries) < len(dm_ids):
        dm_salaries.append(0)

    # 单DM场次薪资必填
    if data['dm_count'] == 1 and dm_salaries[0] <= 0:
        raise ConflictError('单DM场次薪资必须大于0')

    cur = db.execute(
        "INSERT INTO sessions (script_id, dm_count, unit_price, player_count, session_date, "
        "revenue, dm_salary, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (data['script_id'], data['dm_count'], data['unit_price'], data['player_count'],
         data['session_date'], data['revenue'],
         dm_salaries[0] if len(dm_salaries) == 1 else 0,
         data.get('notes', ''), now, now)
    )
    session_id = cur.lastrowid

    for i, dm_id in enumerate(dm_ids):
        db.execute("INSERT INTO session_dms (session_id, dm_id, dm_salary) VALUES (?,?,?)",
                   (session_id, dm_id, dm_salaries[i]))

    db.commit()
    return session_id


def update_session(session_id, data, now=None):
    """编辑场次（事务：UPDATE + 重建 session_dms 关联，支持每DM薪资）。"""
    if now is None:
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    db = get_db()

    existing = db.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not existing:
        raise ConflictError('场次不存在')

    script = db.execute("SELECT id FROM scripts WHERE id = ?", (data['script_id'],)).fetchone()
    if not script:
        raise ConflictError('剧本不存在')

    dm_ids = data['dm_ids']
    if len(dm_ids) != data['dm_count']:
        raise ConflictError('DM人数与DM列表数量不匹配')

    for dm_id in dm_ids:
        dm = db.execute("SELECT id FROM dms WHERE id = ?", (dm_id,)).fetchone()
        if not dm:
            raise ConflictError(f'DM(ID={dm_id})不存在')

    # 每DM薪资
    dm_salaries = data.get('dm_salaries', []) or []
    while len(dm_salaries) < len(dm_ids):
        dm_salaries.append(0)

    if data['dm_count'] == 1 and dm_salaries[0] <= 0:
        raise ConflictError('单DM场次薪资必须大于0')

    db.execute(
        "UPDATE sessions SET script_id=?, dm_count=?, unit_price=?, player_count=?, "
        "session_date=?, revenue=?, dm_salary=?, notes=?, updated_at=? WHERE id=?",
        (data['script_id'], data['dm_count'], data['unit_price'], data['player_count'],
         data['session_date'], data['revenue'],
         dm_salaries[0] if len(dm_salaries) == 1 else 0,
         data.get('notes', ''), now, session_id)
    )

    db.execute("DELETE FROM session_dms WHERE session_id = ?", (session_id,))
    for i, dm_id in enumerate(dm_ids):
        db.execute("INSERT INTO session_dms (session_id, dm_id, dm_salary) VALUES (?,?,?)",
                   (session_id, dm_id, dm_salaries[i]))

    db.commit()


def delete_session(session_id):
    """删除场次（session_dms 级联删除）。"""
    db = get_db()
    db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()
