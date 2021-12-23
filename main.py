#!/usr/bin/env python3

import argparse
import datetime
import textwrap
import os
import re
import yaml

from typing import Optional

DAIRY_ROOT = os.environ.get('DAIRY_ROOT')

EDITORS_CMDS = {
    'vscode': 'code',
    'vim':    'vim',
    'nano':   'nano'
}

class DairyContent(object):
    def __init__(self, date: datetime.datetime = None, content: dict = None):
        if content is not None:
            self._raw_content  = content
            self.date          = datetime.datetime.strptime(content['fecha'], '%d/%m/%Y')
            self.tasks_done    = content.get('tareas-realizadas', [''])
            self.tasks_running = content.get( 'tareas-en-marcha', [''])
            self.tasks_pending = content.get('tareas-pendientes', [''])
            self.asks          = content.get(        'preguntas', [''])
        else:
            self._raw_content  = {}
            self.date          = date
            self.tasks_done    = ['']
            self.tasks_running = ['']
            self.tasks_pending = ['']
            self.asks          = ['']


    def to_dict(self):
        return {
            'fecha'            : self.date.strftime('%d/%m/%Y'),
            'taread-en-marcha' : self.tasks_running,
            'taread-pendientes': self.tasks_pending,
            'taread-realizadas': self.tasks_done,
            'preguntas'        : self.asks,
        }


class Dairy(object):
    _date_fmt = '%Y_%m_%d'
    _re_date_fmt = re.compile(r'\d{4}_\d{2}_\d{2}')

    @static
    def _compute_sub_folder_by_date(date:datetime.datetime) -> str:
        return os.path.join(DAIRY_ROOT, str(date.year), str(date.month))

    @static
    def file_name_to_date(file_name:str) -> datetime.datetime:
        assert (date_match := Dairy._re_date_fmt.search(file_name))
        return datetime.datetime.strptime(Dairy._date_fmt, date_match.group(0))

    @statis
    def FromPath(path:str) -> 'Dairy':
        with open(os.path.join(path) as fs:
            return Dairy(content = yaml.full_load(fs))

    @static
    def FindLast() -> Optional['Dairy']:
        pass

    @static
    def FindByDate(date: datetime.datetime) -> Optional['Dairy']:
        dairy = None
        if os.path.exists(date_folder := Dairy._compute_sub_folder_by_date(date)):
            for file_name in os.listdir(date_folder):
                if date == Dairy.file_name_to_date(file_name):
                    dairy = Dairy.FromPath(os.path.join(date_folder, file_name))
        return dairy

    def __init__(self, date: datetime.datetime):
        self.date      = date
        self.file_name = f"diario_{date.strftime(self._date_fmt)}.yml"
        self._content  = None

    @property
    def sub_folder_path(self) -> str:
        return Dairy._compute_sub_folder_by_date(self.date)

    @property
    def file_path(self) -> str:
        return os.path.join(self.sub_folder_path, self.file_name)

    @property
    def content(self) -> Optional[DairyContent]:
        if self._content is None and os.path.exists(self.file_path):
            with open(self.file_path, 'r') as fs:
                self._content = DairyContent(content = yaml.full_load(fs))

        return self._content

    def create_folders_if_doesnt_exists(self) -> None:
        folder_path = self.sub_folder_path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def create_and_fill(self) -> None:
        with open(self.file_path, 'w') as fs:
            self._content = DairyContent(self.date)
            yaml.dump( self._content.to_dict(), fs, indent=2, default_flow_style=False)

def main(args):
    today = datetime.datetime.now()
    date  = today

    dairy = Dairy(date)
    dairy.create_folders_if_doesnt_exists()

    print("DELETING")
    os.system(f"rm {dairy.file_path}")  #TODO Remove

    if dairy.content is None:
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

