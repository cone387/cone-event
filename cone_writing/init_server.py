import os
import pathlib
from cone_writing import settings


if __name__ == '__main__':
    path = pathlib.Path(__file__).parent
    os.system(f'cd {path} && python manage.py makemigrations')
    os.system(f'cd {path} && python manage.py migrate')
