# -*- coding: utf-8 -*-

import os
import platform
import calendar
import requests
import re
import tqdm

import multiprocessing as mp
from time import sleep
from bs4 import BeautifulSoup
from multiprocessing import Process, Pool
from mantichora import mantichora
from atpbar import atpbar
from korea_news_crawler.exceptions import *
from korea_news_crawler.articleparser import ArticleParser
from korea_news_crawler.writer import Writer

class ArticleCrawler(object):
    def __init__(self, write_root: str = './results/', logger=None):
        self.categories = {
            '정치': 100,
            '경제': 101,
            '사회': 102,
            '생활문화': 103,
            '세계': 104,
            'IT과학': 105,
            '오피니언': 110,
            'politics': 100,
            'economy': 101,
            'society': 102,
            'living_culture': 103,
            'world': 104,
            'IT_science': 105,
            'opinion': 110
        }
        self.selected_categories = []
        self.date = {
            'start_year': 0,
            'start_month': 0,
            'end_year': 0,
            'end_month': 0
        }
        self.user_operating_system = str(platform.system())
        self.write_root = write_root

        self.logger = logger

    def set_category(self, *args):
        """카테고리 설정."""
        for key in args:
            if self.categories.get(key) is None:
                raise InvalidCategory(key)
        self.selected_categories = args

    def set_date_range(self, start_year: int, start_month: int, end_year: int, end_month: int):
        """기간 설정."""
        args = [start_year, start_month, end_year, end_month]
        if start_year > end_year:
            raise InvalidYear(start_year, end_year)
        if start_month < 1 or start_month > 12:
            raise InvalidMonth(start_month)
        if end_month < 1 or end_month > 12:
            raise InvalidMonth(end_month)
        if start_year == end_year and start_month > end_month:
            raise OverbalanceMonth(start_month, end_month)
        for key, date in zip(self.date, args):
            self.date[key] = date

        msg = f"Date configuration: {start_year}.{start_month} ~ {end_year}.{end_month}"
        if self.logger is not None:
            self.logger.info(msg)

    @staticmethod
    def make_news_page_url(category_url, start_year, end_year, start_month, end_month):
        """URL 설정."""
        made_urls = []
        for year in range(start_year, end_year + 1):
            target_start_month = start_month
            target_end_month = end_month

            if start_year != end_year:
                if year == start_year:
                    target_start_month = start_month
                    target_end_month = 12
                elif year == end_year:
                    target_start_month = 1
                    target_end_month = end_month
                else:
                    target_start_month = 1
                    target_end_month = 12
            
            for month in range(target_start_month, target_end_month + 1):
                for month_day in range(1, calendar.monthrange(year, month)[1] + 1):
                    if len(str(month)) == 1:
                        month = "0" + str(month)
                    if len(str(month_day)) == 1:
                        month_day = "0" + str(month_day)
                        
                    # 날짜별로 Page Url 생성
                    url = category_url + str(year) + str(month) + str(month_day)

                    # totalpage는 네이버 페이지 구조를 이용해서 page=10000으로 지정해 totalpage를 알아냄
                    # page=10000을 입력할 경우 페이지가 존재하지 않기 때문에 page=totalpage로 이동 됨 (Redirect)
                    totalpage = ArticleParser.find_news_totalpage(url + "&page=10000")
                    for page in range(1, totalpage + 1):
                        made_urls.append(url + "&page=" + str(page))
        
        return made_urls

    @staticmethod
    def get_url_data(url: str, max_tries: int = 10):
        remaining_tries = int(max_tries)
        while remaining_tries > 0:
            try:
                return requests.get(url, headers={'User-Agent':'Mozilla/5.0'})
            except Exception as e:
                sleep(1)
            remaining_tries = remaining_tries - 1
        return None

    def crawling(self, category_name: str = '경제'):
        """크롤링 시작."""
        
        pid = str(os.getpid())
        if self.logger is not None:
            self.logger.info(f"카테고리:{category_name} | PID: {pid}")
        writer = Writer(category='Article',
                        article_category=category_name,
                        date=self.date,
                        root=self.write_root)
        
        url_format = \
            f"http://news.naver.com/main/list.nhn?mode=LSD&mid=sec&" + \
            f"sid1={self.categories.get(category_name)}&date="
        target_urls = self.make_news_page_url(
            category_url=url_format,
            start_year=self.date['start_year'],
            end_year=self.date['end_year'],
            start_month=self.date['start_month'],
            end_month=self.date['end_month']
        )

        if self.logger is not None:
            self.logger.info(f"URLs generated for {category_name}. Start!")

        # Write headers for csv file
        writer.write_row(['일시', '카테고리', '언론사', '제목', '본문', 'url'])

        #for url in tqdm.tqdm(target_urls, desc=category_name, position=0, leave=True):
        _process = mp.current_process()
        total = len(target_urls)
        position = self.selected_categories.index(category_name)
        with tqdm.tqdm(desc=f"Keyword: {category_name}", total=total, position=position) as pg:
            for url in target_urls:
                request = self.get_url_data(url)
                if request is None:
                    continue
                document = BeautifulSoup(request.content, 'html.parser')

                # html - newsflash_body - type06_headline, type06
                # 각 페이지에 있는 기사들 가져오기
                temp_post = document.select('.newsflash_body .type06_headline li dl')
                temp_post.extend(document.select('.newsflash_body .type06 li dl'))
                
                # 각 페이지에 있는 기사들의 url 저장
                post_urls = []
                for line in temp_post:
                    # 해당되는 page에서 모든 기사들의 URL을 post_urls 리스트에 넣음
                    post_urls.append(line.a.get('href'))
                del temp_post

                # 기사 url
                for content_url in post_urls:
                    # 크롤링 대기 시간
                    sleep(0.01)
                    
                    # 기사 HTML 가져옴
                    request_content = self.get_url_data(content_url)
                    if request_content is None:
                        continue

                    try:
                        document_content = BeautifulSoup(request_content.content, 'html.parser')
                    except:
                        continue

                    try:
                        # 기사 제목 가져옴
                        tag_headline = document_content.find_all('h3', {'id': 'articleTitle'}, {'class': 'tts_head'})
                        # 뉴스 기사 제목 초기화
                        text_headline = ''
                        text_headline = text_headline + ArticleParser.clear_headline(str(tag_headline[0].find_all(text=True)))
                        # 공백일 경우 기사 제외 처리
                        if not text_headline:
                            continue

                        # 기사 본문 가져옴
                        tag_content = document_content.find_all('div', {'id': 'articleBodyContents'})
                        # 뉴스 기사 본문 초기화
                        text_sentence = ''
                        text_sentence = text_sentence + ArticleParser.clear_content(str(tag_content[0].find_all(text=True)))
                        # 공백일 경우 기사 제외 처리
                        if not text_sentence:
                            continue

                        # 기사 언론사 가져옴
                        tag_company = document_content.find_all('meta', {'property': 'me2:category1'})

                        # 언론사 초기화
                        text_company = ''
                        text_company = text_company + str(tag_company[0].get('content'))

                        # 공백일 경우 기사 제외 처리
                        if not text_company:
                            continue

                        # 기사 시간대 가져옴
                        time = re.findall('<span class="t11">(.*)</span>',request_content.text)[0]

                        # CSV 작성
                        writer.write_row([time, category_name, text_company, text_headline, text_sentence, content_url])

                        del time
                        del text_company, text_sentence, text_headline
                        del tag_company 
                        del tag_content, tag_headline
                        del request_content, document_content

                    # UnicodeEncodeError
                    except Exception as ex:
                        del request_content, document_content
                        pass
                pg.update(1)            
        writer.close()


    def start(self, join: bool = True):
        """
        멀티프로세스를 활용한 뉴스 크롤링 시작.
        multiprocessing 패키지 활용.
        """
        procs = []
        for category_name in self.selected_categories:
            proc = Process(target=self.crawling, args=(category_name, ))
            procs.append(proc)
            proc.start()

        if join:
            for proc in procs:
                proc.join()

    def start_pool(self, join: bool = True):
        with mp.Pool(processes=len(self.selected_categories),
                     initializer=tqdm.tqdm.set_lock,
                     initargs=(tqdm.tqdm.get_lock(),)) as pool:
            pool.map(self.crawling, self.selected_categories)
        
    def start_mantichora(self):
        """
        멀티프로세스를 활용한 뉴스 크롤링 시작.
        mantichora 패키지 활용.
        """
        with mantichora(nworkers=len(self.selected_categories)) as mcore:
            for category_name in self.selected_categories:
                mcore.run(self.crawling, category_name)
            results = mcore.returns()

if __name__ == "__main__":
    crawler = ArticleCrawler()
    crawler.set_category('생활문화', 'IT과학')
    crawler.set_date_range(2018, 1, 2018, 2)
    crawler.start()
