"""将 Flask 后端与 Vue 前端打包为可独立运行的 Windows 文件夹程序。

使用方法：
    在 Windows 开发环境中准备 Python 3.10+、Node.js 18+ 和 PATH 中可用的 npm。
    当前 Python 环境需要 flask、Pydantic v2 和 PyInstaller 6+。
    安装示例：python -m pip install flask "pydantic>=2,<3" "pyinstaller>=6"
    从项目根目录执行 python build.py，不接受命令行参数。

构建过程：
    先删除项目中的 build/、dist/ 和 Dianxdian_Manage.spec，再安装缺失的前端依赖、构建并打包。
    首次安装前端依赖可能需要网络；前端依赖已安装时仍会重新执行 npm run build。
    运行前应另行保存旧 dist/ 中的经营数据库、配置及交付压缩包，避免随目录一起删除。

交付方式：
    输出位于 dist/Dianxdian_Manage/，将整个目录复制到目标电脑并运行 Dianxdian_Manage.exe。
    _internal/ 必须保留，目标电脑无需安装 Python 或 Node.js。
    源项目的 database.db、config.json 和 backup/ 不打包；首次运行在程序目录生成运行数据。
"""

import os
import sys
import shutil

# 确保以项目根目录为工作目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# 静态文件查找依赖 PyInstaller 6+ 的 _internal 布局，较低版本会导致页面无法加载。
import PyInstaller
if int(PyInstaller.__version__.split('.')[0]) < 6:
    sys.exit(f'[!] 需要 PyInstaller 6+，当前: {PyInstaller.__version__}')

NAME = 'Dianxdian_Manage'
ENTRY = 'backend/app.py'
FRONTEND_DIST = 'frontend/dist'
HIDDEN_IMPORTS = [
    'pydantic',
    'pydantic.deprecated',
]


def clean_dist():
    """删除旧 build/、dist/ 和 spec 文件，调用前需另行保存交付包中的运行数据。"""
    dirs = ['dist', 'build']
    for d in dirs:
        path = os.path.join(PROJECT_ROOT, d)
        if os.path.isdir(path):
            shutil.rmtree(path)
    spec = os.path.join(PROJECT_ROOT, f'{NAME}.spec')
    if os.path.isfile(spec):
        os.remove(spec)


def build_frontend():
    """必要时安装前端依赖，再调用 npm run build 生成静态文件。"""
    import subprocess
    frontend_dir = os.path.join(PROJECT_ROOT, 'frontend')
    if not os.path.isdir(os.path.join(frontend_dir, 'node_modules')):
        print('[!] 前端依赖未安装，正在安装...')
        subprocess.run('npm install', cwd=frontend_dir, shell=True, check=True)
    print('[>] 构建前端...')
    subprocess.run('npm run build', cwd=frontend_dir, shell=True, check=True)


def run_pyinstaller():
    """将后端入口及 frontend/dist 打包为包含 _internal 的独立程序目录。"""
    import subprocess

    if not os.path.isdir(FRONTEND_DIST):
        print(f'[!] 前端构建产物不存在: {FRONTEND_DIST}')
        sys.exit(1)

    add_data = f'{FRONTEND_DIST};frontend/dist'

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onedir',
        '--name', NAME,
        '--add-data', add_data,
        '--clean',
        '--noconfirm',
    ]

    for mod in HIDDEN_IMPORTS:
        cmd.extend(['--hidden-import', mod])

    cmd.append(ENTRY)

    print(f'[>] 开始打包: {NAME}')
    print(f'[>] 命令: {" ".join(cmd)}')
    subprocess.run(cmd, check=True)


def print_result():
    """打印打包结果提示。"""
    dist_dir = os.path.join(PROJECT_ROOT, 'dist', NAME)
    exe_path = os.path.join(dist_dir, f'{NAME}.exe')
    print()
    if os.path.isfile(exe_path):
        print(f'[√] 打包成功!')
        print(f'    输出目录: {dist_dir}')
        print(f'    启动程序: {exe_path}')
        print()
        print('    部署说明:')
        print(f'    1. 将整个 dist/{NAME} 文件夹拷贝到目标电脑')
        print(f'    2. 双击 {NAME}.exe 启动')
        print('    3. 首次运行自动生成 config.json 和 database.db')
        print('    4. 可选: 创建快捷方式拖入启动文件夹实现开机自启')
    else:
        print('[×] 打包失败，请检查上方错误信息')


if __name__ == '__main__':
    print('[>] 清理旧文件...')
    clean_dist()

    build_frontend()
    run_pyinstaller()
    print_result()
