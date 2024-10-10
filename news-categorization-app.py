# main.py

import feedparser
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from celery import Celery
import spacy
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize SQLAlchemy
Base = declarative_base()
engine = create_engine('postgresql://username:password@localhost/news_db')
Session = sessionmaker(bind=engine)

# Initialize Celery
celery_app = Celery('news_tasks', broker='redis://localhost:6379/0')

# Initialize spaCy
nlp = spacy.load("en_core_web_sm")

# Define the Article model
class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    pub_date = Column(DateTime, nullable=False)
    source_url = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True)

# Create tables
Base.metadata.create_all(engine)

# List of RSS feeds
RSS_FEEDS = [
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "http://qz.com/feed",
    "http://feeds.foxnews.com/foxnews/politics",
    "http://feeds.reuters.com/reuters/businessNews",
    "http://feeds.feedburner.com/NewshourWorld",
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"
]

def parse_feed(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article = {
                'title': entry.title,
                'content': entry.summary,
                'pub_date': datetime(*entry.published_parsed[:6]),
                'source_url': entry.link
            }
            process_article.delay(article)
    except Exception as e:
        logging.error(f"Error parsing feed {feed_url}: {str(e)}")

@celery_app.task
def process_article(article):
    session = Session()
    try:
        # Check for duplicates
        existing = session.query(Article).filter_by(source_url=article['source_url']).first()
        if existing:
            logging.info(f"Duplicate article found: {article['title']}")
            return

        # Categorize the article
        category = categorize_article(article['title'] + " " + article['content'])
        
        # Create new Article object
        new_article = Article(
            title=article['title'],
            content=article['content'],
            pub_date=article['pub_date'],
            source_url=article['source_url'],
            category=category
        )
        
        # Add to database
        session.add(new_article)
        session.commit()
        logging.info(f"Added new article: {article['title']}")
    except Exception as e:
        logging.error(f"Error processing article {article['title']}: {str(e)}")
        session.rollback()
    finally:
        session.close()

def categorize_article(text):
    doc = nlp(text)
    
    # Simple rule-based categorization
    terrorism_keywords = ["terrorism", "protest", "riot", "unrest"]
    positive_keywords = ["positive", "uplifting", "inspiring"]
    disaster_keywords = ["disaster", "earthquake", "flood", "hurricane"]
    
    for token in doc:
        if token.text.lower() in terrorism_keywords:
            return "Terrorism / protest / political unrest / riot"
        elif token.text.lower() in positive_keywords:
            return "Positive/Uplifting"
        elif token.text.lower() in disaster_keywords:
            return "Natural Disasters"
    
    return "Others"

if __name__ == "__main__":
    for feed in RSS_FEEDS:
        parse_feed(feed)
