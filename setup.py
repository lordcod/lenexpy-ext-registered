import os
from pathlib import Path
parent = Path(__file__).parent
packages = parent / '.venv' / 'Lib' / 'site-packages'
filename = parent / 'start.py'

with_console = ''  # '--noconsole'

command = f"pyinstaller \
            --add-data \"config.json;.\" \
            --add-data \"FINA_Points_Table_Base_Times.xlsx;.\" \
            --onedir \
            --paths {packages} \
            --noconfirm {with_console} \
            --workpath ./user/build \
            --distpath ./user/dist \
            -F {filename}"
print(command)
os.system(command)
