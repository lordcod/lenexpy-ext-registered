import os
import sys
from pathlib import Path

# Проверка существования файла config.json
config_path = Path(__file__).parent / 'config.json'
print(f"Does config.json exist? {config_path.exists()}")  # Должно вывести True

# Убедись, что ты в правильной рабочей директории
print("Current working directory:", os.getcwd())

# Путь к файлу
parent = Path(__file__).parent
filename = parent / 'loading.py'

# Консольная опция
with_console = True  # True, если нужна консоль

# Папка для выходного файла
dist_dir = parent / '.user/dist'

# Берём текущий Python, с которого запустили скрипт
venv_python = sys.executable

# Абсолютные пути для файлов
config_file_path = os.path.abspath(config_path)
xlsx_file_path = os.path.abspath(parent / 'FINA_Points_Table_Base_Times.xlsx')

# Базовая команда
command = f"{venv_python} -m nuitka \
    --standalone \
    --output-dir={dist_dir} \
    --remove-output \
    --include-data-files=config.json=config.json \
    --include-data-files=FINA_Points_Table_Base_Times.xlsx=FINA_Points_Table_Base_Times.xlsx \
    --enable-plugin=tk-inter "

# Добавляем опцию для скрытия консоли
if not with_console:
    command += "--windows-console-mode=disable "

# Финальная команда + путь к файлу
command += f"\"{filename}\""

# Вывод команды и выполнение
print(command)
os.system(command)
