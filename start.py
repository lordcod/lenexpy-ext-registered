import json
import traceback
import contextlib
import sys
import os

with contextlib.suppress(Exception):
    os.chdir(sys._MEIPASS)

try:
    from app.menu import App

    with open('config.json', 'rb') as file:
        config = json.loads(file.read())

    app = App(config)
    app.mainloop()
except BaseException:
    traceback.print_exc()
    input()
finally:
    config.pop('lenex', None)
    with open('config.json', 'wb+') as file:
        data = json.dumps(
            config,
            ensure_ascii=False,
            indent=4
        ).encode()
        config = file.write(data)
