"""系统工具 API 路由：提供店铺公开信息、备份和余额校验。"""

from flask import Blueprint, jsonify
from backend.config import DEFAULT_CONFIG, load_config
from backend.services.backup_service import backup_daily
from backend.services.stats_service import verify_balances, fix_balances

bp = Blueprint('system', __name__, url_prefix='/api/system')


@bp.route('/info', methods=['GET'])
def api_system_info():
    """读取店铺名称，仅返回可公开展示的信息。"""
    name = load_config().get('shop_name')
    shop_name = name.strip() if isinstance(name, str) else ''
    return jsonify({'data': {'shop_name': shop_name or DEFAULT_CONFIG['shop_name']}})


@bp.route('/backup', methods=['POST'])
def api_backup():
    """手动触发数据库备份。"""
    filename = backup_daily()
    if filename:
        return jsonify({'message': '备份完成', 'filename': filename})
    return jsonify({'error': '备份失败，数据库文件不存在'}), 404


@bp.route('/verify-balances', methods=['POST'])
def api_verify_balances():
    """手动触发余额一致性校验，自动修复不一致记录。"""
    result = verify_balances()
    if not result['consistent']:
        fix_balances(result['inconsistent_members'])
        result['fixed'] = True
    return jsonify({'data': result})
