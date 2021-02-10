# -*- coding: utf-8, euc-kr -*-

import os
import sys
import time
import logging
import argparse

from rich.console import Console
from datetime import datetime
from dateutil.relativedelta import relativedelta
from korea_news_crawler.articlecrawler import ArticleCrawler


_ = logging.getLogger('urllib3').setLevel(logging.INFO)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)


def parse_arguments():
    """Add function docstring."""
    parser = argparse.ArgumentParser(description='네이버 뉴스기사 크롤링.', add_help=True)
    parser.add_argument('--categories', nargs='+', default=['정치', '경제', '사회', '생활문화', 'IT과학', '세계'],
                        help="'정치', '경제', '사회', '생활문화', 'IT과학', '세계' 중 복수 선택 가능.")
    parser.add_argument('--start_year', type=int, required=True, help="시작년도 (i.e. 2020).")
    parser.add_argument('--start_month', type=int, required=True, help="마침월 (i.e. 11).")
    parser.add_argument('--end_year', type=int, required=True, help="마침년도 (i.e. 2021).")
    parser.add_argument('--end_month', type=int, required=True, help="마침월 (i.e. 1).")
    parser.add_argument('--month_interval', type=int, default=1, help="파일 저장 단위 (개월)")
    parser.add_argument('--join', action='store_true', help="멀티프로세스 동기화 여부.")
    parser.add_argument('--result_dir', type=str, default='./results', help="저장 최상위 디렉토리.")

    return parser.parse_args()


def main():
    """메인 함수."""
    args = parse_arguments()

    logger = logging.getLogger('crawling')
    logger.info(f"Categories: {' '.join(args.categories)}")

    start_date = datetime(args.start_year, args.start_month, 1)                      # 10.01
    end_date = datetime(args.end_year, args.end_month, 1) + relativedelta(months=1)  # 12.01
    end_date = end_date - relativedelta(days=1)

    inter_start_date = start_date                                                    # 10.01
    inter_end_date = start_date + relativedelta(months=args.month_interval)          # 11.01
    inter_end_date = inter_end_date - relativedelta(days=1)

    while True:
        start_time = time.time()

        crawler = ArticleCrawler(
            write_root=os.path.join(args.result_dir, inter_start_date.strftime("%Y_%m")),
            logger=logger
            ) 
        crawler.set_category(*args.categories)
        crawler.set_date_range(
            start_year=inter_start_date.year,
            start_month=inter_start_date.month,
            end_year=inter_end_date.year,
            end_month=inter_end_date.month
        )
        crawler.start(join=args.join)
        if args.join:
            elapsed = time.time() - start_time
            logger.info(f"{crawler.write_root} finished. {elapsed/60:.2f} minutes ({elapsed:.2f} seconds).")

        inter_start_date += relativedelta(months=args.month_interval)  # 11.01 -> 12.01
        inter_end_date   += relativedelta(months=args.month_interval)  # 12.01 -> 01.01

        if inter_end_date > end_date:
            break


if __name__ == '__main__':
    main()
