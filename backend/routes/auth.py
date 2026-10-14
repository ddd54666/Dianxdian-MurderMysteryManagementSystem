"""二级密码验证 API 路由。"""

from flask import Blueprint, request, jsonify, current_app

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/verify-password', methods=['POST'])
def api_verify_password():
    """验证二级密码。"""
    data = request.get_json() or {}
    password = data.get('password', '')
    stored = current_app.config.get('SECONDARY_PASSWORD', 'admin123')

    if password == stored:
        return jsonify({'message': '验证成功', 'valid': True})
    return jsonify({'error': '密码错误', 'valid': False}), 403
