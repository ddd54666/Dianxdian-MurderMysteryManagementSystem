"""测试数据填充脚本：生成覆盖12个月的丰富数据，用于统计页面效果验证。"""

import os
import sys
import random
import sqlite3
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import get_db_path


def now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def seed(db_path=None):
    """主入口：连接数据库并填充全部测试数据。"""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # 先执行建表DDL
    from backend.models.database import _DDL_SCRIPT
    conn.executescript(_DDL_SCRIPT)

    try:
        _seed_all(conn)
        conn.commit()
        print(f'[OK] 测试数据已写入 {db_path}')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _seed_all(db):
    """按依赖顺序填充所有表。"""
    scripts = _seed_scripts(db)
    dms = _seed_dms(db)
    _seed_sessions(db, scripts, dms)
    members = _seed_members(db)
    _seed_recharges(db, members)
    _seed_consumptions(db, members)
    _seed_carpools(db, scripts)
    _seed_messages(db)
    print(f'    剧本 {len(scripts)}   DM {len(dms)}   会员 {len(members)}')


def _seed_scripts(db):
    """12个剧本：覆盖5种类型+盒装/城限，不同价位和人数。"""
    data = [
        # name, type, category, unit_price(分), player_count, is_fixed
        ('雪乡连环杀人事件', '推理', '盒装', 7800, 6, 1),
        ('来电', '欢乐', '盒装', 6800, 6, 1),
        ('病娇男孩的精分日记', '恐怖', '盒装', 8800, 7, 1),
        ('告别诗', '情感', '城限', 12800, 6, 1),
        ('拆迁', '机制', '盒装', 7800, 10, 1),
        ('年轮', '推理', '盒装', 8800, 5, 1),
        ('霜降', '情感', '城限', 13800, 6, 1),
        ('马丁内斯死在惊奇馆', '推理', '盒装', 9800, 6, 0),
        ('漓川怪谈簿', '推理', '城限', 15800, 7, 0),
        ('青楼', '欢乐', '盒装', 7800, 7, 0),
        ('古木吟', '恐怖', '城限', 11800, 6, 1),
        ('孤城', '机制', '盒装', 8800, 7, 0),
    ]
    ids = []
    for name, tp, cat, price, count, fixed in data:
        ts = now()
        db.execute(
            'INSERT INTO scripts (name, type, category, unit_price, player_count, is_player_count_fixed, created_at, updated_at) '
            'VALUES (?,?,?,?,?,?,?,?)',
            (name, tp, cat, price, count, fixed, ts, ts)
        )
        ids.append(db.execute('SELECT last_insert_rowid()').fetchone()[0])
    return ids


def _seed_dms(db):
    """8个DM：多样化的名字。"""
    data = ['点点', '小黛', '聿', '阿杰', '老王', '小鹿', '大海', '圆圆']
    ids = []
    for name in data:
        ts = now()
        db.execute('INSERT INTO dms (name, notes, created_at) VALUES (?,?,?)', (name, '', ts))
        ids.append(db.execute('SELECT last_insert_rowid()').fetchone()[0])
    return ids


def _seed_sessions(db, script_ids, dm_ids):
    """填充场次：覆盖最近12个月，每月8-15场，含单DM和多DM，多DM薪资随机分配。"""
    scripts_info = {
        row[0]: row for row in db.execute(
            'SELECT id, unit_price, player_count FROM scripts'
        ).fetchall()
    }
    today = date.today()
    session_count = 0

    for month_offset in range(11, -1, -1):  # 最近12个月
        year = today.year
        month = today.month - month_offset
        if month <= 0:
            month += 12
            year -= 1

        # 每月8-15场，越近越多
        base = 8 if month_offset > 6 else 10 if month_offset > 2 else 12
        n_sessions = random.randint(base, base + 3)
        days = random.sample(range(1, 28), n_sessions)
        days.sort()

        for day in days:
            sid = random.choice(script_ids)
            info = scripts_info[sid]
            base_price = info['unit_price']

            # 折扣：大部分原价，少数打折
            discount = random.choices([1.0, 0.9, 0.85, 0.8], weights=[50, 25, 15, 10])[0]
            actual_price = max(1, int(base_price * discount))
            player_count = info['player_count']
            if random.random() < 0.15:
                player_count = max(2, player_count + random.choice([-2, -1, 1]))

            # DM人数：单DM 60%，双DM 30%，三DM 10%
            dm_count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            dm_count = min(dm_count, len(dm_ids))
            selected_dms = random.sample(dm_ids, dm_count)
            revenue = actual_price * player_count

            # 每DM薪资：单DM时取单价80-100%，多DM时随机分配
            dm_salaries = []
            if dm_count == 1:
                dm_salaries = [int(actual_price * random.uniform(0.8, 1.0))]
            else:
                # 多DM：总薪资约为单价的60-90%，分配给各DM
                total_salary = int(actual_price * random.uniform(0.6, 0.9))
                # 随机拆分
                parts = [random.random() for _ in range(dm_count)]
                total_parts = sum(parts)
                dm_salaries = [max(100, int(total_salary * p / total_parts / 100) * 100) for p in parts]

            session_date = f'{year}-{month:02d}-{day:02d}'
            ts = f'{session_date}T{random.randint(10, 22):02d}:{random.randint(0, 59):02d}:00'
            notes_pool = ['', '', '客人要求延长时间', '新人局', '翻车了😂', '', '老顾客优惠',
                          '会员日', '周末场', '电话预约', '', '']
            notes = random.choice(notes_pool)

            # sessions表dm_salary：单DM存实际值，多DM存0（向后兼容）
            session_dm_salary = dm_salaries[0] if dm_count == 1 else 0
            db.execute(
                'INSERT INTO sessions (script_id, dm_count, unit_price, player_count, session_date, revenue, dm_salary, notes, created_at, updated_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?)',
                (sid, dm_count, actual_price, player_count, session_date, revenue, session_dm_salary, notes, ts, ts)
            )
            session_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

            for i, did in enumerate(selected_dms):
                db.execute(
                    'INSERT INTO session_dms (session_id, dm_id, dm_salary) VALUES (?,?,?)',
                    (session_id, did, dm_salaries[i])
                )
            session_count += 1

    print(f'    场次 {session_count} 条', end='  ')


def _seed_members(db):
    """12个会员：不同余额等级。"""
    data = [
        ('张伟', '男', '13800001111', 50000, '喜欢推理本'),
        ('李娜', '女', '13800002222', 120000, '老顾客，常带朋友'),
        ('王磊', '男', '13800003333', 8000, ''),
        ('赵敏', '女', '13800004444', 35000, '只玩情感本'),
        ('孙鹏', '男', '13800005555', 200000, '老板的朋友，大客户'),
        ('周雪', '女', '13800006666', 10000, ''),
        ('吴昊', '男', '13800007777', 65000, '喜欢恐怖本和机制本'),
        ('陈静', '女', '13800008888', 45000, ''),
        ('刘洋', '男', '13800009999', 180000, '每周必来'),
        ('黄丽', '女', '13800010000', 25000, '新会员'),
        ('马超', '男', '13800011111', 95000, ''),
        ('林芳', '女', '13800012222', 55000, '推荐来的'),
    ]
    ids = []
    for name, gender, phone, balance, notes in data:
        ts = now()
        db.execute(
            'INSERT INTO members (name, gender, phone, balance, notes, created_at, updated_at) '
            'VALUES (?,?,?,?,?,?,?)',
            (name, gender, phone, balance, notes, ts, ts)
        )
        ids.append(db.execute('SELECT last_insert_rowid()').fetchone()[0])
    return ids


def _seed_recharges(db, member_ids):
    """为每个会员生成初始充值 + 2-5条后续充值，模拟真实充值节奏。"""
    members = db.execute('SELECT id, name, phone, balance FROM members').fetchall()
    count = 0
    for m in members:
        # 初始充值（3-12个月前）
        days_ago = random.randint(90, 365)
        initial_time = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S')
        initial = int(m['balance'] * random.uniform(0.3, 0.6))
        bonus = random.choice([0, 0, 0, 5000, 10000, 20000])
        db.execute(
            'INSERT INTO recharges (member_id, member_name, member_phone, recharge_time, pay_amount, bonus_amount, created_at) '
            'VALUES (?,?,?,?,?,?,?)',
            (m['id'], m['name'], m['phone'], initial_time, initial, bonus, initial_time)
        )
        count += 1

        # 后续充值 2-5条
        for _ in range(random.randint(2, 5)):
            rt = (datetime.now() - timedelta(days=random.randint(5, 180))).strftime('%Y-%m-%dT%H:%M:%S')
            pay = random.choice([10000, 10000, 20000, 20000, 30000, 50000, 100000])
            bonus2 = random.choice([0, 0, 0, 0, 0, 5000, 10000])
            db.execute(
                'INSERT INTO recharges (member_id, member_name, member_phone, recharge_time, pay_amount, bonus_amount, created_at) '
                'VALUES (?,?,?,?,?,?,?)',
                (m['id'], m['name'], m['phone'], rt, pay, bonus2, rt)
            )
            count += 1
    print(f'充值 {count} 条', end='  ')


def _seed_consumptions(db, member_ids):
    """为每个会员生成消费记录：大部分来自脚本价格，覆盖近6个月。"""
    members = db.execute('SELECT id, name, phone FROM members').fetchall()
    prices = [6800, 7800, 8800, 9800, 12800, 13800, 15800, 11800]
    script_names = ['雪乡', '来电', '病娇', '告别诗', '拆迁', '年轮', '霜降', '马丁内斯', '漓川', '青楼', '古木吟', '孤城']
    count = 0
    for m in members:
        n = random.randint(5, 12)  # 每人5-12条消费
        for _ in range(n):
            ct = (datetime.now() - timedelta(days=random.randint(3, 180))).strftime('%Y-%m-%dT%H:%M:%S')
            amount = random.choice(prices)
            sn = random.choice(script_names)
            db.execute(
                'INSERT INTO consumptions (member_id, member_name, member_phone, consumption_time, amount, script_name, created_at) '
                'VALUES (?,?,?,?,?,?,?)',
                (m['id'], m['name'], m['phone'], ct, amount, sn, ct)
            )
            count += 1
    print(f'消费 {count} 条', end='  ')


def _seed_carpools(db, script_ids):
    """填充15条拼车记录：近期和未来都有。"""
    today = date.today()
    notes_pool = [
        '3=4 差1男', '差小黛 差聿', '2=5 等3人', '满车',
        '差2女', '', '周末拼车 已有3人', '急缺1人 今晚发车',
        '4=2 差两人', '女生局 已有4人', '工作日晚上 差3人',
        '新手局 欢迎新人', '', '5=1 差一人成团', '老手局 速来'
    ]
    count = 0
    for i in range(15):
        d = today + timedelta(days=random.randint(-7, 10))
        sd = d.strftime('%Y-%m-%d')
        sid = random.choice(script_ids)
        ts = now()
        notes = random.choice(notes_pool)
        db.execute(
            'INSERT INTO carpools (carpool_date, script_id, notes, created_at, updated_at) '
            'VALUES (?,?,?,?,?)',
            (sd, sid, notes, ts, ts)
        )
        count += 1
    print(f'拼车 {count} 条', end='  ')


def _seed_messages(db):
    """12条留言：贴近真实聊天内容。"""
    data = [
        ('老板JJ', '建议加个剧本推荐功能！根据客人喜好推荐本子。'),
        ('点点', '今天雪乡翻车了，新人太难带了😂'),
        ('小黛', '系统挺好用的！拼车功能很方便。'),
        ('聿', '昨天霜降开了两场，累死我了。'),
        ('老板JJ', '最近生意不错，考虑加新剧本。'),
        ('阿杰', '会员张伟余额快没了，提醒一下。'),
        ('点点', '统计图表真清晰，给老板看了一目了然。'),
        ('老王', '希望手机上也能用，不在店里想看看排班。'),
        ('老板JJ', '下周进货：马丁内斯和漓川怪谈簿。'),
        ('小鹿', '周五晚上拼车差一人，谁来？'),
        ('大海', '古木吟真的绝了！推荐给所有客人。'),
        ('圆圆', '今天接待了一桌生日局，客人很开心。'),
    ]
    for author, content in data:
        days_ago = random.randint(0, 30)
        ts = (datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))).strftime('%Y-%m-%dT%H:%M:%S')
        db.execute('INSERT INTO messages (author, content, created_at) VALUES (?,?,?)', (author, content, ts))
    print(f'留言 {len(data)} 条')


if __name__ == '__main__':
    seed()
