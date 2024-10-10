# run_parser.py

from main import parse_feed, RSS_FEEDS
import schedule
import time

def job():
    for feed in RSS_FEEDS:
        parse_feed(feed)

schedule.every(1).hour.do(job)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
