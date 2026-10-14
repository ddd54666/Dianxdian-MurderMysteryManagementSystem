"""场次管理 API 路由。"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from backend.models.session_model import (
    list_sessions, get_session, create_session, update_session, delete_session
)
from backend.models.script_model import ConflictError
from backend.schemas.schemas import SessionCreate, SessionUpdate
from backend.utils import format_validation_errors

bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')


@bp.route('', methods=['GET'])
def api_list_sessions():
    """场次列表（分页+筛选，默认本月）。"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    stype = request.args.get('type')
    dm_id = request.args.get('dm_id', type=int)
    script_id = request.args.get('script_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_sessions(year, month, stype, dm_id, script_id, page, page_size))


@bp.route('/<int:session_id>', methods=['GET'])
def api_get_session(session_id):
    """场次详情。"""
    row = get_session(session_id)
    if not row:
        return jsonify({'error': '场次不存在'}), 404
    return jsonify({'data': row})


@bp.route('', methods=['POST'])
def api_create_session():
    """新增场次。"""
    try:
        data = SessionCreate(**request.get_json()).model_dump()
        sid = create_session(data)
        row = get_session(sid)
        return jsonify({'data': row, 'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/<int:session_id>', methods=['PUT'])
def api_update_session(session_id):
    """编辑场次。"""
    try:
        data = SessionUpdate(**request.get_json()).model_dump()
        update_session(session_id, data)
        row = get_session(session_id)
        return jsonify({'data': row, 'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/<int:session_id>', methods=['DELETE'])
def api_delete_session(session_id):
    """删除场次。"""
    delete_session(session_id)
    return jsonify({'message': '删除成功'})
