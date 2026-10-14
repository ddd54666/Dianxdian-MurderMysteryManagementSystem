"""剧本管理 API 路由。"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from backend.models.script_model import (
    list_scripts, search_scripts, get_script_by_id,
    create_script, update_script, delete_script, ConflictError
)
from backend.schemas.schemas import ScriptCreate, ScriptUpdate
from backend.utils import format_validation_errors

bp = Blueprint('scripts', __name__, url_prefix='/api/scripts')


@bp.route('', methods=['GET'])
def api_list_scripts():
    """剧本列表（分页+筛选）。"""
    search = request.args.get('search')
    stype = request.args.get('type')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_scripts(search, stype, category, page, page_size))


@bp.route('/search', methods=['GET'])
def api_search_scripts():
    """剧本名称模糊搜索（自动补全）。"""
    q = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    if len(q) < 1:
        return jsonify({'data': []})
    return jsonify({'data': search_scripts(q, limit)})


@bp.route('/<int:script_id>', methods=['GET'])
def api_get_script(script_id):
    """剧本详情。"""
    row = get_script_by_id(script_id)
    if not row:
        return jsonify({'error': '剧本不存在'}), 404
    return jsonify({'data': dict(row)})


@bp.route('', methods=['POST'])
def api_create_script():
    """新增剧本。"""
    try:
        data = ScriptCreate(**request.get_json()).model_dump()
        sid = create_script(data)
        row = get_script_by_id(sid)
        return jsonify({'data': dict(row), 'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/<int:script_id>', methods=['PUT'])
def api_update_script(script_id):
    """编辑剧本。"""
    try:
        data = ScriptUpdate(**request.get_json()).model_dump()
        update_script(script_id, data)
        row = get_script_by_id(script_id)
        return jsonify({'data': dict(row), 'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/<int:script_id>', methods=['DELETE'])
def api_delete_script(script_id):
    """删除剧本。"""
    try:
        delete_script(script_id)
        return jsonify({'message': '删除成功'})
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409
