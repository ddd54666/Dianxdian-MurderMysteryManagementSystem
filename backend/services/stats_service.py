"""统计服务：营业额、剧本场次、DM开本统计，余额校验，CSV导出。"""

import csv
import io
from datetime import datetime, date, timedelta
from backend.models.database import get_db


def _build_date_filter(year, month):
    """构造 SQL 日期筛选条件和参数。"""
    if year and month:
        return "AND s.session_date LIKE ?", (f"{year}-{month:02d}%",)
    if year:
        return "AND s.session_date LIKE ?", (f"{year}-%",)
    return "", ()


def get_revenue_overview():
    """总览卡片数据：今日/本周/本月/本年营业额与场次数。"""
    db = get_db()
    today = date.today()
    # 本周一
    week_start = today - timedelta(days=today.weekday())

    today_str = today.strftime('%Y-%m-%d')
    week_str = week_start.strftime('%Y-%m-%d')
    month_str = today.strftime('%Y-%m')
    year_str = today.strftime('%Y')

    def _query(date_clause, params):
        row = db.execute(f"""
            SELECT COALESCE(SUM(revenue),0) AS revenue, COUNT(*) AS session_count
            FROM sessions WHERE {date_clause}
        """, params).fetchone()
        return {'revenue': row[0], 'session_count': row[1]}

    return {
        'today': _query("session_date = ?", (today_str,)),
        'this_week': _query("session_date >= ?", (week_str,)),
        'this_month': _query("session_date LIKE ?", (month_str + '%',)),
        'this_year': _query("session_date LIKE ?", (year_str + '%',))
    }


def get_revenue_stats(year, month):
    """营业额统计：月趋势(含场均)、日趋势(仅按月时)、年度对比、按类型、按种类、汇总。"""
    db = get_db()
    clause, params = _build_date_filter(year, month)

    monthly = db.execute(f"""
        SELECT substr(s.session_date,1,7) AS month,
               SUM(s.revenue) AS revenue,
               COUNT(*) AS session_count,
               CASE WHEN COUNT(*) > 0 THEN CAST(SUM(s.revenue)/COUNT(*) AS INTEGER) ELSE 0 END AS avg_revenue_per_session
        FROM sessions s WHERE 1=1 {clause}
        GROUP BY month ORDER BY month
    """, params).fetchall()

    # 日趋势仅在按月模式下返回
    daily = []
    if year and month:
        daily = db.execute("""
            SELECT s.session_date AS date,
                   SUM(s.revenue) AS revenue,
                   COUNT(*) AS session_count,
                   CASE WHEN COUNT(*) > 0 THEN CAST(SUM(s.revenue)/COUNT(*) AS INTEGER) ELSE 0 END AS avg_revenue_per_session
            FROM sessions s
            WHERE s.session_date LIKE ?
            GROUP BY s.session_date ORDER BY s.session_date
        """, (f"{year}-{month:02d}%",)).fetchall()

    yearly = db.execute("""
        SELECT substr(s.session_date,1,4) AS year,
               SUM(s.revenue) AS revenue
        FROM sessions s
        GROUP BY year ORDER BY year
    """).fetchall()

    by_type = db.execute(f"""
        SELECT sc.type, SUM(s.revenue) AS revenue
        FROM sessions s JOIN scripts sc ON s.script_id = sc.id
        WHERE 1=1 {clause}
        GROUP BY sc.type
    """, params).fetchall()

    by_category = db.execute(f"""
        SELECT sc.category, SUM(s.revenue) AS revenue
        FROM sessions s JOIN scripts sc ON s.script_id = sc.id
        WHERE 1=1 {clause}
        GROUP BY sc.category
    """, params).fetchall()

    by_script = db.execute(f"""
        SELECT sc.name AS script_name, sc.type AS script_type,
               SUM(s.revenue) AS revenue, COUNT(*) AS session_count,
               RANK() OVER (ORDER BY SUM(s.revenue) DESC) AS rank
        FROM sessions s JOIN scripts sc ON s.script_id = sc.id
        WHERE 1=1 {clause}
        GROUP BY sc.id ORDER BY revenue DESC
    """, params).fetchall()

    summary = db.execute(f"""
        SELECT COALESCE(SUM(s.revenue),0) AS total_revenue,
               COUNT(*) AS total_sessions,
               CASE WHEN COUNT(*) > 0 THEN CAST(SUM(s.revenue)/COUNT(*) AS INTEGER) ELSE 0 END AS avg_revenue_per_session
        FROM sessions s WHERE 1=1 {clause}
    """, params).fetchone()

    return {
        'monthly_trend': [dict(r) for r in monthly],
        'daily_trend': [dict(r) for r in daily],
        'yearly_comparison': [dict(r) for r in yearly],
        'by_type': [dict(r) for r in by_type],
        'by_category': [dict(r) for r in by_category],
        'by_script': [dict(r) for r in by_script],
        'summary': dict(summary) if summary else {'total_revenue': 0, 'total_sessions': 0, 'avg_revenue_per_session': 0}
    }


def get_script_stats(year, month):
    """剧本场次统计：排行、按类型/种类分布、月趋势、日趋势、汇总。"""
    db = get_db()
    clause, params = _build_date_filter(year, month)

    ranking = db.execute(f"""
        SELECT sc.name AS script_name, sc.id AS script_id, sc.type AS script_type,
               COUNT(*) AS count, RANK() OVER (ORDER BY COUNT(*) DESC) AS rank
        FROM sessions s JOIN scripts sc ON s.script_id = sc.id
        WHERE 1=1 {clause}
        GROUP BY sc.id ORDER BY count DESC
    """, params).fetchall()

    by_type = db.execute(f"""
        SELECT sc.type, COUNT(*) AS count
        FROM sessions s JOIN scripts sc ON s.script_id = sc.id
        WHERE 1=1 {clause}
        GROUP BY sc.type
    """, params).fetchall()

    by_category = db.execute(f"""
        SELECT sc.category, COUNT(*) AS count
        FROM sessions s JOIN scripts sc ON s.script_id = sc.id
        WHERE 1=1 {clause}
        GROUP BY sc.category
    """, params).fetchall()

    monthly_trend = db.execute(f"""
        SELECT substr(s.session_date,1,7) AS month, COUNT(*) AS count
        FROM sessions s WHERE 1=1 {clause}
        GROUP BY month ORDER BY month
    """, params).fetchall()

    daily_trend = []
    if year and month:
        daily_trend = db.execute("""
            SELECT s.session_date AS date, COUNT(*) AS count
            FROM sessions s
            WHERE s.session_date LIKE ?
            GROUP BY s.session_date ORDER BY s.session_date
        """, (f"{year}-{month:02d}%",)).fetchall()

    summary = db.execute(f"""
        SELECT COUNT(*) AS total_sessions
        FROM sessions s WHERE 1=1 {clause}
    """, params).fetchone()

    return {
        'ranking': [dict(r) for r in ranking],
        'by_type': [dict(r) for r in by_type],
        'by_category': [dict(r) for r in by_category],
        'monthly_trend': [dict(r) for r in monthly_trend],
        'daily_trend': [dict(r) for r in daily_trend],
        'summary': dict(summary) if summary else {'total_sessions': 0}
    }


def get_script_detail(script_id):
    """单个剧本统计：本月/今年场次、近6个月趋势。"""
    db = get_db()
    today = date.today()
    month_str = today.strftime('%Y-%m')
    year_str = today.strftime('%Y')

    this_month = db.execute("""
        SELECT COUNT(*) FROM sessions
        WHERE script_id = ? AND session_date LIKE ?
    """, (script_id, month_str + '%')).fetchone()[0]

    this_year = db.execute("""
        SELECT COUNT(*) FROM sessions
        WHERE script_id = ? AND session_date LIKE ?
    """, (script_id, year_str + '%')).fetchone()[0]

    # 近13个月趋势
    months = []
    for i in range(12, -1, -1):
        d = today.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        months.append(d.strftime('%Y-%m'))

    trend = []
    for m in months:
        count = db.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE script_id = ? AND session_date LIKE ?
        """, (script_id, m + '%')).fetchone()[0]
        trend.append({'month': m, 'count': count})

    return {
        'this_month_count': this_month,
        'this_year_count': this_year,
        'trend_13months': trend
    }


def get_dm_stats(year, month):
    """DM开本统计：排行（含每DM薪资）、日趋势（仅按月时）。"""
    db = get_db()
    clause, params = _build_date_filter(year, month)

    ranking = db.execute(f"""
        SELECT d.id AS dm_id, d.name AS dm_name,
               COUNT(sd.session_id) AS session_count,
               COALESCE(SUM(sd.dm_salary),0) AS total_salary,
               COALESCE(SUM(s.revenue),0) AS total_revenue
        FROM session_dms sd
        JOIN sessions s ON sd.session_id = s.id
        JOIN dms d ON sd.dm_id = d.id
        WHERE 1=1 {clause}
        GROUP BY d.id ORDER BY session_count DESC
    """, params).fetchall()

    summary = db.execute(f"""
        SELECT COUNT(DISTINCT sd.dm_id) AS active_dm_count,
               COUNT(DISTINCT sd.session_id) AS total_sessions
        FROM session_dms sd
        JOIN sessions s ON sd.session_id = s.id
        WHERE 1=1 {clause}
    """, params).fetchone()

    return {
        'ranking': [dict(r) for r in ranking],
        'summary': dict(summary) if summary else {'active_dm_count': 0, 'total_sessions': 0}
    }


def get_dm_detail(dm_id):
    """单个DM统计：本月/今年开本数+薪资、近13个月趋势（含每月薪资）。"""
    db = get_db()
    today = date.today()
    month_str = today.strftime('%Y-%m')
    year_str = today.strftime('%Y')

    def _query(date_like):
        row = db.execute("""
            SELECT COUNT(sd.session_id),
                   COALESCE(SUM(sd.dm_salary), 0)
            FROM session_dms sd
            JOIN sessions s ON sd.session_id = s.id
            WHERE sd.dm_id = ? AND s.session_date LIKE ?
        """, (dm_id, date_like)).fetchone()
        return {'count': row[0], 'salary': row[1]}

    this_month = _query(month_str + '%')
    this_year = _query(year_str + '%')

    # 近13个月趋势
    months = []
    for i in range(12, -1, -1):
        d = today.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        months.append(d.strftime('%Y-%m'))

    trend = []
    for m in months:
        r = _query(m + '%')
        trend.append({'month': m, 'count': r['count'], 'salary': r['salary']})

    return {
        'this_month_count': this_month['count'],
        'this_year_count': this_year['count'],
        'this_month_salary': this_month['salary'],
        'this_year_salary': this_year['salary'],
        'trend_13months': trend
    }


def verify_balances():
    """校验所有会员余额与交易记录的一致性。返回不一致的会员列表。"""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM (
            SELECT m.id AS member_id, m.name AS member_name,
                   m.balance AS stored_balance,
                   COALESCE((SELECT SUM(r.pay_amount + r.bonus_amount) FROM recharges r
                             WHERE r.member_id = m.id AND r.deleted_at IS NULL), 0)
                   - COALESCE((SELECT SUM(c.amount) FROM consumptions c
                               WHERE c.member_id = m.id AND c.deleted_at IS NULL), 0)
                   AS calculated_balance
            FROM members m
        ) WHERE stored_balance != calculated_balance
    """).fetchall()

    inconsistent = []
    for row in rows:
        r = dict(row)
        r['diff'] = r['stored_balance'] - r['calculated_balance']
        inconsistent.append(r)

    return {'consistent': len(inconsistent) == 0, 'inconsistent_members': inconsistent}


def fix_balances(inconsistent):
    """根据交易记录修正会员余额。"""
    if not inconsistent:
        return
    db = get_db()
    for item in inconsistent:
        db.execute("UPDATE members SET balance = ? WHERE id = ?",
                   (item['calculated_balance'], item['member_id']))
    db.commit()


def export_sessions_csv(year, month):
    """导出全部场次明细为 CSV（金额转为元）。"""
    db = get_db()
    clause, params = _build_date_filter(year, month)

    rows = db.execute(f"""
        SELECT s.session_date, sc.name AS script_name, sc.type AS script_type,
               sc.category AS script_category,
               GROUP_CONCAT(d.name, '、') AS dms,
               s.player_count, s.unit_price, s.revenue, s.dm_salary, s.notes
        FROM sessions s
        JOIN scripts sc ON s.script_id = sc.id
        LEFT JOIN session_dms sd ON s.id = sd.session_id
        LEFT JOIN dms d ON sd.dm_id = d.id
        WHERE 1=1 {clause}
        GROUP BY s.id ORDER BY s.session_date DESC
    """, params).fetchall()

    output = io.StringIO()
    output.write('﻿')  # BOM，确保 Excel 正确识别中文
    writer = csv.writer(output)
    writer.writerow(['开本日期', '剧本名称', '剧本类型', '剧本种类', 'DM',
                     '人数', '单价(元)', '营业额(元)', 'DM薪资(元)', '备注'])

    for row in rows:
        r = dict(row)
        writer.writerow([
            r['session_date'],
            r['script_name'],
            r['script_type'],
            r['script_category'],
            r['dms'] or '',
            r['player_count'],
            f"{r['unit_price'] / 100:.2f}",
            f"{r['revenue'] / 100:.2f}",
            f"{r['dm_salary'] / 100:.2f}",
            r['notes'] or ''
        ])

    return output.getvalue()
