"""DM管理 API 路由。"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from backend.models.dm_model import (
    list_dms, search_dms, get_dm_by_id, create_dm,
    update_dm, delete_dm, get_dm_sessions
)
from backend.models.script_model import ConflictError
from backend.schemas.schemas import DMCreate, DMUpdate
from backend.utils import format_validation_errors

bp = Blueprint('dms', __name__, url_prefix='/api/dms')


@bp.route('', methods=['GET'])
def api_list_dms():
    """DM列表（分页+搜索，默认按本月开本次数降序）。"""
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_dms(search, page, page_size))


@bp.route('/search', methods=['GET'])
def api_search_dms():
    """DM姓名模糊搜索（自动补全）。"""
    q = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    if len(q) < 1:
        return jsonify({'data': []})
    return jsonify({'data': search_dms(q, limit)})


@bp.route('', methods=['POST'])
def api_create_dm():
    """新增DM。"""
    try:
        data = DMCreate(**request.get_json()).model_dump()
        did = create_dm(data)
        row = get_dm_by_id(did)
        return jsonify({'data': dict(row), 'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400


@bp.route('/<int:dm_id>', methods=['PUT'])
def api_update_dm(dm_id):
    """编辑DM。"""
    try:
        data = DMUpdate(**request.get_json()).model_dump()
        update_dm(dm_id, data)
        row = get_dm_by_id(dm_id)
        return jsonify({'data': dict(row), 'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400


@bp.route('/<int:dm_id>', methods=['DELETE'])
def api_delete_dm(dm_id):
    """删除DM。"""
    try:
        delete_dm(dm_id)
        return jsonify({'message': '删除成功'})
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/<int:dm_id>/sessions', methods=['GET'])
def api_dm_sessions(dm_id):
    """DM开本历史。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(get_dm_sessions(dm_id, page, page_size))
