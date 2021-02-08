import csv
import platform
from korea_news_crawler.exceptions import *


class Writer(object):
    def __init__(self,
                 category: str,
                 article_category: str,
                 date: dict,
                 root: str = './results'
                 ):
        
        self.start_year = date['start_year']
        self.start_month = f'0{date["start_month"]}' if len(str(date['start_month'])) == 1 else str(date['start_month'])
        self.end_year = date['end_year']
        self.end_month = f'0{date["end_month"]}' if len(str(date['end_month'])) == 1 else str(date['end_month'])

        self.root = root
        os.makedirs(root, exist_ok=True)

        self.file = None
        self.initialize_file(category, article_category)
        self.csv_writer = csv.writer(self.file)

    def initialize_file(self, category: str = 'Article', article_category: str = '경제'):
        """결과를 저장할 파일 생성."""
        
        filename = \
            f"{category}_{article_category}" + "_" + \
            f"{self.start_year}{self.start_month}" + "_" + \
            f"{self.end_year}{self.end_month}.csv"
        filename = os.path.join(self.root, filename)
        if os.path.isfile(filename):
            raise ExistFile(filename)

        os_type = str(platform.system())
        if os_type == 'Windows':
            self.file = open(filename, 'w', encoding='euc-kr', newline='')
        else:
            self.file = open(filename, 'w', encoding='cp949', newline='')  # {cp949, utf-8}

    def write_row(self, arg: list):
        self.csv_writer.writerow(arg)

    def close(self):
        self.file.close()
