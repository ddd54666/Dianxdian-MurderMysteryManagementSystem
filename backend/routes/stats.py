"""统计信息 API 路由。"""

from flask import Blueprint, request, jsonify, Response
from backend.services.stats_service import (
    get_revenue_stats, get_revenue_overview, get_script_stats, get_script_detail,
    get_dm_stats, get_dm_detail, export_sessions_csv
)

bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@bp.route('/revenue/overview', methods=['GET'])
def api_revenue_overview():
    """营业额总览卡片（今日/本周/本月/本年）。"""
    return jsonify({'data': get_revenue_overview()})


@bp.route('/revenue', methods=['GET'])
def api_revenue_stats():
    """营业额统计。"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({'data': get_revenue_stats(year, month)})


@bp.route('/scripts', methods=['GET'])
def api_script_stats():
    """剧本场次统计。"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({'data': get_script_stats(year, month)})


@bp.route('/scripts/<int:script_id>/detail', methods=['GET'])
def api_script_detail(script_id):
    """单个剧本详情统计。"""
    return jsonify({'data': get_script_detail(script_id)})


@bp.route('/dms', methods=['GET'])
def api_dm_stats():
    """DM开本统计。"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return jsonify({'data': get_dm_stats(year, month)})


@bp.route('/dms/<int:dm_id>/detail', methods=['GET'])
def api_dm_detail(dm_id):
    """单个DM详情统计。"""
    return jsonify({'data': get_dm_detail(dm_id)})


@bp.route('/export/summary', methods=['GET'])
def api_export_summary():
    """导出汇总CSV（按当前统计视图）。"""
    stype = request.args.get('type', 'revenue')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if stype == 'revenue':
        data = get_revenue_stats(year, month)
        csv_content = _revenue_summary_csv(data)
    elif stype == 'scripts':
        data = get_script_stats(year, month)
        csv_content = _scripts_summary_csv(data)
    elif stype == 'dms':
        data = get_dm_stats(year, month)
        csv_content = _dms_summary_csv(data)
    else:
        return jsonify({'error': '无效的导出类型'}), 400

    return Response(csv_content, mimetype='text/csv; charset=utf-8-sig',
                    headers={'Content-Disposition': f'attachment; filename={stype}_summary.csv'})


@bp.route('/export/detail', methods=['GET'])
def api_export_detail():
    """导出场次明细CSV。"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    csv_content = export_sessions_csv(year, month)
    return Response(csv_content, mimetype='text/csv; charset=utf-8-sig',
                    headers={'Content-Disposition': 'attachment; filename=sessions_detail.csv'})


def _revenue_summary_csv(data):
    """营业额汇总转CSV。"""
    import csv, io
    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output)
    summary = data.get('summary', {})
    w.writerow(['总营业额(元)', '总场次', '场均营业额(元)'])
    w.writerow([
        f"{summary.get('total_revenue',0)/100:.2f}",
        summary.get('total_sessions', 0),
        f"{summary.get('avg_revenue_per_session',0)/100:.2f}"
    ])
    return output.getvalue()


def _scripts_summary_csv(data):
    """剧本统计汇总转CSV。"""
    import csv, io
    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output)
    w.writerow(['排名', '剧本名称', '场次数'])
    for r in data.get('ranking', []):
        w.writerow([r.get('rank', ''), r.get('script_name', ''), r.get('count', 0)])
    return output.getvalue()


def _dms_summary_csv(data):
    """DM统计汇总转CSV。"""
    import csv, io
    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output)
    w.writerow(['DM姓名', '开本次数', '总薪资(元)', '总营业额(元)'])
    for r in data.get('ranking', []):
        w.writerow([
            r.get('dm_name', ''),
            r.get('session_count', 0),
            f"{r.get('total_salary',0)/100:.2f}",
            f"{r.get('total_revenue',0)/100:.2f}"
        ])
    return output.getvalue()
