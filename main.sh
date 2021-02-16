echo "Crawling..."
YEAR=1996
python main.py \
    --categories 정치 \
    --start_year $YEAR \
    --start_month 1 \
    --end_year $YEAR \
    --end_month 12
echo "Finished."
