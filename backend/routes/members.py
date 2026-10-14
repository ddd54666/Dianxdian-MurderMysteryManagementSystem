"""会员管理 API 路由（含充值/消费子路由）。"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from backend.models.member_model import (
    list_members, get_member, create_member, update_member,
    list_recharges, create_recharge, update_recharge, delete_recharge,
    list_consumptions, create_consumption, update_consumption, delete_consumption
)
from backend.models.script_model import ConflictError
from backend.schemas.schemas import (
    MemberCreate, MemberUpdate, RechargeCreate, ConsumptionCreate
)
from backend.utils import format_validation_errors

bp = Blueprint('members', __name__, url_prefix='/api')


@bp.route('/members', methods=['GET'])
def api_list_members():
    """会员列表（分页+搜索）。"""
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_members(search, page, page_size))


@bp.route('/members/<int:member_id>', methods=['GET'])
def api_get_member(member_id):
    """会员详情（含交易记录）。"""
    row = get_member(member_id)
    if not row:
        return jsonify({'error': '会员不存在'}), 404
    return jsonify({'data': row})


@bp.route('/members', methods=['POST'])
def api_create_member():
    """新增会员（需二级密码，前端控制）。"""
    try:
        data = MemberCreate(**request.get_json()).model_dump()
        mid = create_member(data)
        row = get_member(mid)
        return jsonify({'data': row, 'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/members/<int:member_id>', methods=['PUT'])
def api_update_member(member_id):
    """编辑会员信息。"""
    try:
        data = MemberUpdate(**request.get_json()).model_dump()
        update_member(member_id, data)
        row = get_member(member_id)
        return jsonify({'data': row, 'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/members/<int:member_id>/recharges', methods=['GET'])
def api_list_recharges(member_id):
    """会员充值列表。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_recharges(member_id, page, page_size))


@bp.route('/members/<int:member_id>/recharges', methods=['POST'])
def api_create_recharge(member_id):
    """新增充值。"""
    try:
        data = RechargeCreate(**request.get_json()).model_dump()
        create_recharge(member_id, data)
        return jsonify({'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/recharges/<int:recharge_id>', methods=['PUT'])
def api_update_recharge(recharge_id):
    """编辑充值记录。"""
    try:
        data = RechargeCreate(**request.get_json()).model_dump()
        update_recharge(recharge_id, data)
        return jsonify({'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/recharges/<int:recharge_id>', methods=['DELETE'])
def api_delete_recharge(recharge_id):
    """软删除充值记录。"""
    try:
        delete_recharge(recharge_id)
        return jsonify({'message': '删除成功'})
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/members/<int:member_id>/consumptions', methods=['GET'])
def api_list_consumptions(member_id):
    """会员消费列表。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_consumptions(member_id, page, page_size))


@bp.route('/members/<int:member_id>/consumptions', methods=['POST'])
def api_create_consumption(member_id):
    """新增消费。"""
    try:
        data = ConsumptionCreate(**request.get_json()).model_dump()
        create_consumption(member_id, data)
        return jsonify({'message': '新增成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/consumptions/<int:consumption_id>', methods=['PUT'])
def api_update_consumption(consumption_id):
    """编辑消费记录。"""
    try:
        data = ConsumptionCreate(**request.get_json()).model_dump()
        update_consumption(consumption_id, data)
        return jsonify({'message': '修改成功'})
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/consumptions/<int:consumption_id>', methods=['DELETE'])
def api_delete_consumption(consumption_id):
    """软删除消费记录。"""
    try:
        delete_consumption(consumption_id)
        return jsonify({'message': '删除成功'})
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409
