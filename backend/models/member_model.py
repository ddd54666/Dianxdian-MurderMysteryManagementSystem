"""会员、充值、消费数据操作层。所有余额变更均在事务中完成。"""

from datetime import datetime
from backend.models.database import get_db
from backend.models.script_model import ConflictError


def _now_iso():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def list_members(search=None, page=1, page_size=20):
    """分页查询会员列表，支持姓名或电话搜索。"""
    db = get_db()
    conditions, params = [], []

    if search:
        conditions.append("(name LIKE ? OR phone LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = db.execute(f"SELECT COUNT(*) FROM members {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT * FROM members m {where} ORDER BY m.created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()

    return {'data': [dict(r) for r in rows], 'total': total, 'page': page, 'page_size': page_size}


def get_member(member_id):
    """获取会员详情（含最近20条充值+消费记录）。"""
    db = get_db()
    member = db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        return None

    recharges = db.execute(
        "SELECT * FROM recharges WHERE member_id = ? AND deleted_at IS NULL "
        "ORDER BY recharge_time DESC LIMIT 20",
        (member_id,)
    ).fetchall()

    consumptions = db.execute(
        "SELECT * FROM consumptions WHERE member_id = ? AND deleted_at IS NULL "
        "ORDER BY consumption_time DESC LIMIT 20",
        (member_id,)
    ).fetchall()

    result = dict(member)
    result['recharges'] = [dict(r) for r in recharges]
    result['consumptions'] = [dict(r) for r in consumptions]
    return result


def create_member(data, now=None):
    """新增会员（事务：INSERT member + 首条充值记录，余额=初始充值）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    existing = db.execute("SELECT id FROM members WHERE phone = ?", (data['phone'],)).fetchone()
    if existing:
        raise ConflictError('该手机号已注册会员')

    pay = data['pay_amount']
    bonus = data.get('bonus_amount', 0)

    cur = db.execute(
        "INSERT INTO members (name, gender, phone, balance, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (data['name'], data['gender'], data['phone'], pay + bonus,
         data.get('notes', ''), now, now)
    )
    member_id = cur.lastrowid

    db.execute(
        "INSERT INTO recharges (member_id, member_name, member_phone, recharge_time, "
        "pay_amount, bonus_amount, created_at) VALUES (?,?,?,?,?,?,?)",
        (member_id, data['name'], data['phone'], now, pay, bonus, now)
    )

    db.commit()
    return member_id


def update_member(member_id, data):
    """编辑会员信息（不修改余额）。"""
    db = get_db()

    existing = db.execute("SELECT phone FROM members WHERE phone = ? AND id != ?",
                          (data['phone'], member_id)).fetchone()
    if existing:
        raise ConflictError('该手机号已被其他会员使用')

    db.execute(
        "UPDATE members SET name=?, gender=?, phone=?, notes=? WHERE id=?",
        (data['name'], data['gender'], data['phone'], data.get('notes', ''), member_id)
    )
    db.commit()


def list_recharges(member_id, page=1, page_size=20):
    """查询会员充值记录（过滤软删除）。"""
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM recharges WHERE member_id = ? AND deleted_at IS NULL",
        (member_id,)
    ).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        "SELECT * FROM recharges WHERE member_id = ? AND deleted_at IS NULL "
        "ORDER BY recharge_time DESC LIMIT ? OFFSET ?",
        (member_id, page_size, offset)
    ).fetchall()

    return {'data': [dict(r) for r in rows], 'total': total, 'page': page, 'page_size': page_size}


def create_recharge(member_id, data, now=None):
    """新增充值（事务：INSERT recharge + UPDATE balance）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    member = db.execute("SELECT name, phone FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        raise ConflictError('会员不存在')

    pay = data['pay_amount']
    bonus = data.get('bonus_amount', 0)

    db.execute(
        "INSERT INTO recharges (member_id, member_name, member_phone, recharge_time, "
        "pay_amount, bonus_amount, created_at) VALUES (?,?,?,?,?,?,?)",
        (member_id, member['name'], member['phone'],
         data.get('recharge_time', now), pay, bonus, now)
    )

    db.execute("UPDATE members SET balance = balance + ?, updated_at = ? WHERE id = ?",
               (pay + bonus, now, member_id))

    db.commit()


def update_recharge(recharge_id, data, now=None):
    """编辑充值记录（事务：回滚旧金额 + 应用新金额 + UPDATE 记录）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    old = db.execute(
        "SELECT member_id, pay_amount, bonus_amount FROM recharges WHERE id = ? AND deleted_at IS NULL",
        (recharge_id,)
    ).fetchone()
    if not old:
        raise ConflictError('充值记录不存在')

    old_total = old['pay_amount'] + old['bonus_amount']
    new_pay = data['pay_amount']
    new_bonus = data.get('bonus_amount', 0)
    new_total = new_pay + new_bonus

    member = db.execute("SELECT balance FROM members WHERE id = ?", (old['member_id'],)).fetchone()
    if member['balance'] - old_total + new_total < 0:
        raise ConflictError('余额不足，无法修改')

    db.execute("UPDATE members SET balance = balance - ? + ?, updated_at = ? WHERE id = ?",
               (old_total, new_total, now, old['member_id']))

    db.execute(
        "UPDATE recharges SET recharge_time=?, pay_amount=?, bonus_amount=? WHERE id=?",
        (data.get('recharge_time', now), new_pay, new_bonus, recharge_id)
    )

    db.commit()


def delete_recharge(recharge_id, now=None):
    """软删除充值记录（事务：回滚金额 + SET deleted_at）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    old = db.execute(
        "SELECT member_id, pay_amount, bonus_amount FROM recharges WHERE id = ? AND deleted_at IS NULL",
        (recharge_id,)
    ).fetchone()
    if not old:
        raise ConflictError('充值记录不存在或已删除')

    member = db.execute("SELECT balance FROM members WHERE id = ?", (old['member_id'],)).fetchone()
    if member['balance'] - (old['pay_amount'] + old['bonus_amount']) < 0:
        raise ConflictError('余额不足，无法删除')

    db.execute("UPDATE members SET balance = balance - ?, updated_at = ? WHERE id = ?",
               (old['pay_amount'] + old['bonus_amount'], now, old['member_id']))

    db.execute("UPDATE recharges SET deleted_at = ? WHERE id = ?", (now, recharge_id))

    db.commit()


def list_consumptions(member_id, page=1, page_size=20):
    """查询会员消费记录（过滤软删除）。"""
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM consumptions WHERE member_id = ? AND deleted_at IS NULL",
        (member_id,)
    ).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        "SELECT * FROM consumptions WHERE member_id = ? AND deleted_at IS NULL "
        "ORDER BY consumption_time DESC LIMIT ? OFFSET ?",
        (member_id, page_size, offset)
    ).fetchall()

    return {'data': [dict(r) for r in rows], 'total': total, 'page': page, 'page_size': page_size}


def create_consumption(member_id, data, now=None):
    """新增消费（事务：校验余额充足 + INSERT + UPDATE balance）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    member = db.execute("SELECT name, phone, balance FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        raise ConflictError('会员不存在')

    amount = data['amount']
    if amount > member['balance']:
        raise ConflictError('余额不足')

    db.execute(
        "INSERT INTO consumptions (member_id, member_name, member_phone, consumption_time, "
        "amount, script_name, created_at) VALUES (?,?,?,?,?,?,?)",
        (member_id, member['name'], member['phone'],
         data.get('consumption_time', now), amount, data['script_name'], now)
    )

    db.execute("UPDATE members SET balance = balance - ?, updated_at = ? WHERE id = ?", (amount, now, member_id))

    db.commit()


def update_consumption(consumption_id, data, now=None):
    """编辑消费记录（事务：回滚旧金额 + 应用新金额 + UPDATE 记录）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    old = db.execute(
        "SELECT member_id, amount FROM consumptions WHERE id = ? AND deleted_at IS NULL",
        (consumption_id,)
    ).fetchone()
    if not old:
        raise ConflictError('消费记录不存在')

    new_amount = data['amount']
    member = db.execute("SELECT balance FROM members WHERE id = ?", (old['member_id'],)).fetchone()
    if member['balance'] + old['amount'] - new_amount < 0:
        raise ConflictError('余额不足，无法修改')

    db.execute("UPDATE members SET balance = balance + ? - ?, updated_at = ? WHERE id = ?",
               (old['amount'], new_amount, now, old['member_id']))

    db.execute(
        "UPDATE consumptions SET consumption_time=?, amount=?, script_name=? WHERE id=?",
        (data.get('consumption_time', now), new_amount, data['script_name'], consumption_id)
    )

    db.commit()


def delete_consumption(consumption_id, now=None):
    """软删除消费记录（事务：回滚金额 + SET deleted_at）。"""
    if now is None:
        now = _now_iso()
    db = get_db()

    old = db.execute(
        "SELECT member_id, amount FROM consumptions WHERE id = ? AND deleted_at IS NULL",
        (consumption_id,)
    ).fetchone()
    if not old:
        raise ConflictError('消费记录不存在或已删除')

    db.execute("UPDATE members SET balance = balance + ?, updated_at = ? WHERE id = ?",
               (old['amount'], now, old['member_id']))

    db.execute("UPDATE consumptions SET deleted_at = ? WHERE id = ?", (now, consumption_id))

    db.commit()
