#!/usr/bin/env python3

import argparse
import datetime
import textwrap
import os
import re
import yaml

from typing import Optional, List

DAIRY_ROOT = os.environ.get('DAIRY_ROOT')

EDITORS_CMDS = {
    'vscode': 'code',
    'vim':    'vim',
    'nano':   'nano'
}

class DairyContent(object):
    def __init__(
        self,
        date     : datetime.datetime = None,
        content  : dict              = None,
        prv_dairy: Optional['Dairy'] = None
    ):
        if content is not None:
            self._raw_content  = content
            self.date          = datetime.datetime.strptime(content['fecha'], '%d/%m/%Y')
            self.tasks_done    = content.get('tareas-realizadas', [''])
            self.tasks_running = content.get( 'tareas-en-marcha', [''])
            self.tasks_pending = content.get('tareas-pendientes', [''])
            self.asks          = content.get(        'preguntas', [''])
        else:
            self.date          = date
            self.tasks_done    = ['']
            self.asks          = ['']
            self.tasks_running = ['']

            if prv_dairy is None:
                self.tasks_pending = ['']
            else:
                prv_content        = prv_dairy._content
                self.tasks_pending = []
                for f in (prv_content.tasks_running + prv_content.tasks_pending):
                    self.tasks_pending.append(f)
                
                if len(self.tasks_pending) == 0:
                    self.tasks_pending = ['']

            self._raw_content  = self.to_dict()

    def to_dict(self):
        return {
            'fecha'            : self.date.strftime('%d/%m/%Y'),
            'tareas-en-marcha' : self.tasks_running,
            'tareas-pendientes': self.tasks_pending,
            'tareas-realizadas': self.tasks_done,
            'preguntas'        : self.asks,
        }


class Dairy(object):
    _date_fmt = '%Y_%m_%d'
    _re_date_fmt     = re.compile(r'\d{4}_\d{2}_\d{2}')
    _re_filename_fmt = re.compile(r'^diario_\d{4}_\d{2}_\d{2}\.yml$')

    @staticmethod
    def _compute_sub_folder_by_date(date:datetime.datetime) -> str:
        return os.path.join(DAIRY_ROOT, str(date.year), str(date.month))
    
    @staticmethod
    def valid_file_name_fmt(file_name: str) -> bool:
        return Dairy._re_filename_fmt.search(file_name) is not None

    @staticmethod
    def file_name_to_date(file_name:str) -> datetime.datetime:
        assert (date_match := Dairy._re_date_fmt.search(file_name))
        return datetime.datetime.strptime(date_match.group(0), Dairy._date_fmt)

    @staticmethod
    def date_to_file_name(date:datetime.datetime) -> str:
        return f"diario_{date.strftime(Dairy._date_fmt)}.yml"

    @staticmethod
    def FromPath(path:str) -> 'Dairy':
        with open(os.path.join(path), 'r') as fs:
            dairy_content  = DairyContent(content = yaml.full_load(fs))
            dairy          = Dairy(dairy_content.date)
            dairy._content = dairy_content
            return dairy

    @staticmethod
    def FindLast() -> Optional['Dairy']:
        pass

    @staticmethod
    def FindByDate(date: datetime.datetime) -> Optional['Dairy']:
        dairy = None
        date_folder = Dairy._compute_sub_folder_by_date(date)
        if os.path.exists(file_path := os.path.join(date_folder, Dairy.date_to_file_name(date))):
            dairy = Dairy.FromPath(file_path)
        return dairy

    def __init__(self, date: datetime.datetime):
        self.date      = date
        self.file_name = Dairy.date_to_file_name(date)
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

    def create_and_fill(self, prev_dairy:Optional['Dairy'] = None) -> None:
        with open(self.file_path, 'w') as fs:
            self._content = DairyContent(self.date, prv_dairy=prev_dairy)
            yaml.dump( self._content.to_dict(), fs, indent=2, default_flow_style=False)


class FileManager():
    _cache_path = './cache'
    _dairies_log_file_name = '.dairies_logs.log'
    _dairies_log_path      = os.path.join(_cache_path, _dairies_log_file_name)
    _date_dairy_log_fmt    = '%Y%m%d'

    def _all_dairies_to_log_records(self) -> List[str]:
        dairies_dates = []
        for (_, _, file_names) in os.walk(DAIRY_ROOT):
            for f_name in file_names:
                if Dairy.valid_file_name_fmt(f_name):
                    dairies_dates.append(
                        Dairy.file_name_to_date(f_name).strftime(self._date_dairy_log_fmt))
        
        return dairies_dates
    
    def _init_dairies_log(self):
        with open(self._dairies_log_path, 'w') as fs:
            fs.write('')
            for date_str in self._all_dairies_to_log_records():
                fs.write(f'\n{date_str}')

    def settup(self):

        if not os.path.exists(self._cache_path):
            os.makedirs(self._cache_path)

        if not os.path.exists(self._dairies_log_path):
            self._init_dairies_log()

    def last_dairy_before(self, date: datetime.datetime) -> Optional[Dairy]:
        with open(self._dairies_log_path, 'r') as fs:
            if len(lines := fs.readlines()) == 0:
                return None
            
            lines_dates = [datetime.datetime.strptime(l.strip(), self._date_dairy_log_fmt)
                            for l in lines if l.strip()]
            valid_dates = [d for d in (lines_dates) if d < date]
            if len(valid_dates) == 0:
                return None

            return Dairy.FindByDate(sorted(valid_dates)[-1])

    def insert_dairy_in_log(self, dairy: Dairy):
        with open(self._dairies_log_path, 'a') as fs:
            fs.write('\n' + dairy.date.strftime(self._date_dairy_log_fmt))


def main(args):
    file_manager = FileManager()
    file_manager.settup()

    today = datetime.datetime.strptime(
        datetime.datetime.now().strftime('%Y%m%d'), '%Y%m%d')
    date  = today

    dairy = Dairy(date)
    dairy.create_folders_if_doesnt_exists()

    if dairy.content is None:
        dairy.create_and_fill(file_manager.last_dairy_before(date))
        file_manager.insert_dairy_in_log(dairy)

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

