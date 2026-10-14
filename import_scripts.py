"""从 Excel 批量导入剧本，跳过数据库中已存在的同名记录。

使用方法：
    在项目根目录执行 python -m pip install openpyxl，随后执行 python import_scripts.py。
    默认读取当前工作目录中的 data.xlsx，写入项目根目录的 database.db。
    自定义文件路径时调用 import_scripts(xlsx_path=文件路径)，主入口不解析命令行参数。
    导入前建议停止正在运行的系统并备份数据库；导入会直接修改现有剧本库。

Excel 格式：
    使用 .xlsx 文件，将目标工作表保存为活动工作表；脚本只读取 wb.active。
    第1行为表头，从第2行开始导入；按列位置读取，不校验表头文字，至少保留 A-F 六列。
    A列：剧本名称，必填文本，首尾空格会被去除。
    B列：类型，只接受 欢乐、推理、恐怖、情感、机制。
    C列：种类，只接受 盒装、城限。
    D列：单价，单位为元，必须大于0；填写数值，建议最多保留两位小数。
    E列：玩家人数，应填写大于0的整数。
    F列：是否固定人数，建议明确填写 是 或 否；空值默认按 是 处理。
    固定人数也接受字符串 1、Y、y、yes、Yes，其余非空文本按不固定处理。
    当前实现会将数字0和布尔False也视为默认值；不固定人数请填写 否，避免歧义。
    G列及之后的数据忽略。请勿使用合并单元格、公式或带“元”“人”等单位的数值文本。

示例行：
    示例剧本 | 推理 | 盒装 | 88 | 6 | 是

处理规则：
    名称相同的剧本只跳过，不更新原有信息；无效行输出错误后继续处理其他行。
    单价使用 int(float(单价) * 100) 转为分，多余精度会截断，不执行四舍五入。
    玩家人数使用 int() 转换，数字小数会被截断，因此源表应直接填写整数。
    有效行在循环结束后提交，出现无效行不代表整批导入回滚。重复执行不会覆盖同名记录。
"""

import os
import sys
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import load_workbook
from backend.config import get_db_path
from backend.models.database import _DDL_SCRIPT

VALID_TYPES = {'欢乐', '推理', '恐怖', '情感', '机制'}
VALID_CATEGORIES = {'盒装', '城限'}


def import_scripts(xlsx_path='data.xlsx'):
    """读取指定工作簿的活动工作表，校验六列字段并导入未重名的剧本。"""
    if not os.path.exists(xlsx_path):
        print(f'[错误] 找不到文件: {xlsx_path}')
        return

    db_path = get_db_path()
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript(_DDL_SCRIPT)
    # 按原始单元格值读取，不计算公式；仅处理工作簿的活动工作表。
    wb = load_workbook(xlsx_path)
    ws = wb.active

    inserted = 0
    skipped = 0
    total = 0
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    # 首行固定作为表头跳过，后续数据必须保持 A-F 的列顺序。
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or len(row) < 6:
            continue

        # 列: A=剧本名称 B=类型 C=种类 D=单价(元) E=玩家人数 F=是否固定人数
        try:
            name = str(row[0]).strip() if row[0] else ''
            script_type = str(row[1]).strip() if row[1] else ''
            category = str(row[2]).strip() if row[2] else ''
            unit_price_yuan = row[3]
            player_count = row[4]
            is_fixed_raw = str(row[5]).strip() if row[5] else '是'
        except IndexError:
            print(f'[错误] 第{i}行: 列数不足')
            continue

        # 必填校验
        if not name:
            print(f'[错误] 第{i}行: 剧本名称为空')
            continue

        total += 1

        # 类型校验
        if script_type not in VALID_TYPES:
            print(f'[错误] 第{i}行 "{name}": 类型 "{script_type}" 无效，需为 欢乐/推理/恐怖/情感/机制')
            continue

        # 种类校验
        if category not in VALID_CATEGORIES:
            print(f'[错误] 第{i}行 "{name}": 种类 "{category}" 无效，需为 盒装/城限')
            continue

        # 单价校验
        try:
            unit_price_fen = int(float(unit_price_yuan) * 100)
        except (TypeError, ValueError):
            print(f'[错误] 第{i}行 "{name}": 单价 "{unit_price_yuan}" 无效')
            continue
        if unit_price_fen <= 0:
            print(f'[错误] 第{i}行 "{name}": 单价必须大于0')
            continue

        # 人数校验
        try:
            player_count = int(player_count)
        except (TypeError, ValueError):
            print(f'[错误] 第{i}行 "{name}": 玩家人数 "{player_count}" 无效')
            continue
        if player_count <= 0:
            print(f'[错误] 第{i}行 "{name}": 玩家人数必须大于0')
            continue

        # 推荐源表填写“是”或“否”，避免数字0被上方默认值逻辑当作“是”。
        is_fixed = 1 if is_fixed_raw in ('是', '1', 'Y', 'y', 'yes', 'Yes') else 0

        # 检查重复
        existing = db.execute(
            'SELECT id FROM scripts WHERE name = ?', (name,)
        ).fetchone()

        if existing:
            print(f'[跳过] 剧本已存在: {name}')
            skipped += 1
            continue

        try:
            db.execute(
                'INSERT INTO scripts (name, type, category, unit_price, player_count, '
                'is_player_count_fixed, created_at, updated_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (name, script_type, category, unit_price_fen, player_count, is_fixed, now, now)
            )
            print(f'[导入] {name} ({script_type}/{category} {unit_price_fen/100:.0f}元 {player_count}人 {"固定" if is_fixed else "不固定"})')
            inserted += 1
        except Exception as e:
            print(f'[错误] 导入失败 {name}: {e}')

    db.commit()
    db.close()
    wb.close()
    print(f'\n完成: 导入 {inserted} 条, 跳过 {skipped} 条 (有效数据 {total} 行)')


if __name__ == '__main__':
    import_scripts()
