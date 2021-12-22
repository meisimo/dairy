#!/usr/bin/env python3

import argparse
import datetime
import textwrap
import os

DAIRY_ROOT = os.environ.get('DAIRY_ROOT')

EDITORS_CMDS = {
    'vscode': 'code',
    'vim':    'vim',
    'nano':   'nano'
}


class Dairy(object):
    def __init__(self, date: datetime.datetime):
        self.date      = date
        self.file_name = f"diario_{date.strftime('%Y_%m_%d')}.yml"

    @property
    def sub_folder_path(self) -> str:
        return os.path.join(DAIRY_ROOT, str(self.date.year), str(self.date.month))

    @property
    def file_path(self) -> str:
        return os.path.join(self.sub_folder_path, self.file_name)

    @property
    def content(self) -> str:
        if not os.path.exists(self.file_path):
            return ''

        with open(self.file_path, 'r+') as fs:
            return fs.read().strip()

    def create_folders_if_doesnt_exists(self) -> None:
        folder_path = self.sub_folder_path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def create_and_fill(self) -> None:
        with open(self.file_path, 'a') as fs:
            fs.write(textwrap.dedent(f"""
                fecha: {self.date.strftime('%d/%m/%Y')}
                tareas-realizadas:
                taraes-en-marcha:
                preguntas:
                pendientes:
                """).strip())

def main(args):
    today = datetime.datetime.now()
    date  = today

    dairy = Dairy(date)
    dairy.create_folders_if_doesnt_exists()

    if dairy.content == '':
        dairy.create_and_fill()

    os.system(EDITORS_CMDS[args.editor] + " " + dairy.file_path)


def _get_input():
    args_parser = argparse.ArgumentParser(description="Gestor del diario")
    args_parser.add_argument('--editor', '-e',
                            action='store',
                            choices=EDITORS_CMDS.keys(),
                            default='vim',
                            help=f'Ejige un editor para abrir las notas. Editores: {", ".join(EDITORS_CMDS.keys())} . Por defecto: VIM')
    return args_parser.parse_args()

if __name__ == "__main__":
    main(_get_input())

