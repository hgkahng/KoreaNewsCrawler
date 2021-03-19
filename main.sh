echo "Crawling..."
YEAR=2020
python main.py \
    --categories 정치 사회 경제 IT과학 \
    --start_year $YEAR \
    --start_month 1 \
    --end_year $YEAR \
    --end_month 12 \
    --join
echo "Finished."
