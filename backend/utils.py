"""供后端路由使用的请求校验错误中文格式化工具，不是独立命令行脚本。

使用方法：
    路由捕获 Pydantic ValidationError 后，将异常的 errors() 结果传入此模块的函数。
    例如 format_validation_errors([{'type': 'missing', 'loc': ('phone',)}]) 返回“手机号为必填项”。
    返回结果为用中文分号连接的字符串，可放入 JSON 的 error 字段并返回 HTTP 400。
    直接执行此文件不会启动服务、处理请求或修改数据库。
"""


def format_validation_errors(errors):
    """将 Pydantic errors() 列表转换为中文错误字符串，空列表返回通用校验提示。"""

    # 字段名中英文对照
    field_names = {
        'name': '姓名',
        'phone': '手机号',
        'gender': '性别',
        'type': '剧本类型',
        'category': '剧本种类',
        'unit_price': '单价',
        'player_count': '人数',
        'script_name': '剧本名称',
        'script_id': '剧本',
        'dm_ids': 'DM列表',
        'dm_count': 'DM人数',
        'dm_salary': 'DM薪资',
        'revenue': '营业额',
        'session_date': '开本日期',
        'carpool_date': '拼车日期',
        'initial_charge': '初始充值',
        'pay_amount': '实付金额',
        'bonus_amount': '赠送金额',
        'amount': '金额',
        'recharge_time': '充值时间',
        'consumption_time': '消费时间',
        'author': '留言者',
        'content': '留言内容',
        'is_player_count_fixed': '人数固定',
        'notes': '备注',
        'password': '密码',
    }

    messages = []
    for err in errors:
        loc = err.get('loc', [])
        field = loc[-1] if loc else '未知字段'
        label = field_names.get(str(field), str(field))

        err_type = err.get('type', '')
        ctx = err.get('ctx', {})

        if err_type == 'missing':
            messages.append(f'{label}为必填项')
        elif err_type == 'string_too_short':
            messages.append(f'{label}长度不足')
        elif err_type == 'string_type':
            messages.append(f'{label}格式错误')
        elif err_type == 'value_error':
            messages.append(err.get('msg', f'{label}格式不正确'))
        elif err_type == 'less_than_equal':
            messages.append(f'{label}数值超出范围')
        elif err_type == 'greater_than':
            messages.append(f'{label}必须大于0')
        elif err_type == 'greater_than_equal':
            messages.append(f'{label}不能为负数')
        elif err_type == 'int_type':
            messages.append(f'{label}必须为整数')
        elif err_type == 'bool_type':
            messages.append(f'{label}格式错误')
        elif 'unique' in str(err_type).lower() or 'unique' in err.get('msg', ''):
            messages.append(f'{label}已存在')
        else:
            messages.append(f'{label}: {err.get("msg", "校验失败")}')

    return '；'.join(messages) if messages else '请求参数校验失败'
