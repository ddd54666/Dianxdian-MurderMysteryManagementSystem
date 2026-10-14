"""留言板 API 路由。"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from backend.models.message_model import list_messages, create_message, delete_message
from backend.schemas.schemas import MessageCreate
from backend.utils import format_validation_errors

bp = Blueprint('messages', __name__, url_prefix='/api/messages')


@bp.route('', methods=['GET'])
def api_list_messages():
    """留言列表（分页，倒序）。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    return jsonify(list_messages(page, page_size))


@bp.route('', methods=['POST'])
def api_create_message():
    """新增留言。"""
    try:
        data = MessageCreate(**request.get_json()).model_dump()
        mid = create_message(data)
        return jsonify({'data': {'id': mid}, 'message': '发布成功'}), 201
    except ValidationError as e:
        return jsonify({'error': format_validation_errors(e.errors())}), 400


@bp.route('/<int:message_id>', methods=['DELETE'])
def api_delete_message(message_id):
    """删除留言。"""
    delete_message(message_id)
    return jsonify({'message': '删除成功'})
