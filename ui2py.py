"""Compile all .ui files to .py files"""

import subprocess
from pathlib import Path

ui_dir = Path('ui')
py_dir = ui_dir / 'uic'
py_dir.mkdir(exist_ok=True)

ui_files = ui_dir.glob('*.ui')
for ui_file in ui_files:
    py_file = py_dir / f'{ui_file.stem}.py'
    subprocess.check_call(f'pyside6-uic {ui_file} -o {py_file}')
