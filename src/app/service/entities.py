import os
import uuid
import shutil
from collections import namedtuple
from app import config

ExecuteResult = namedtuple('ExecuteResult', ('result', 'error'))


class KotlinFile:

    """ Описывает файлы, необходимые для запуска программы """

    FILE_NAME = 'Main'
    ENTRY_CLASS = 'MainKt'

    def __init__(self, code: str):
        file_id = uuid.uuid4()
        self.work_dir = os.path.join(config.SANDBOX_DIR, str(file_id))
        os.makedirs(self.work_dir, mode=0o777, exist_ok=True)
        self.filepath_kt = os.path.join(
            self.work_dir, f'{self.FILE_NAME}.kt'
        )
        with open(self.filepath_kt, 'w') as file:
            file.write(code)

    def remove(self):
        try:
            shutil.rmtree(self.work_dir)
        except:
            pass
