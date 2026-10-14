"""拼车管理 API 路由。"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from backend.models.carpool_model import list_carpools, create_carpool, update_carpool, delete_carpool
from backend.schemas.schemas import CarpoolCreate, CarpoolUpdate
from backend.utils import format_validation_errors

bp = Blueprint('carpools', __name__, url_prefix='/api/carpools')


@bp.route('', methods=['GET'])
def api_list_carpools():
    """拼车列表（分页）。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_carpools(page, page_size))


@bp.route('', methods=['POST'])
def api_create_carpool():
    """新增拼车。"""
    try:
        data = CarpoolCreate(**request.get_json()).model_dump()
        cid = create_carpool(data)
        return jsonify({'data': {'id': cid}, 'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400


@bp.route('/<int:carpool_id>', methods=['PUT'])
def api_update_carpool(carpool_id):
    """编辑拼车。"""
    try:
        data = CarpoolUpdate(**request.get_json()).model_dump()
        update_carpool(carpool_id, data)
        return jsonify({'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400


@bp.route('/<int:carpool_id>', methods=['DELETE'])
def api_delete_carpool(carpool_id):
    """删除拼车。"""
    delete_carpool(carpool_id)
    return jsonify({'message': '删除成功'})
