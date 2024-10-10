# In main.py, add this function:

import json
from sqlalchemy.orm import class_mapper

def export_data(format='json'):
    session = Session()
    try:
        articles = session.query(Article).all()
        
        if format == 'json':
            def serialize(model):
                columns = [c.key for c in class_mapper(model.__class__).columns]
                return {c: getattr(model, c) for c in columns}
            
            data = [serialize(article) for article in articles]
            with open('articles_export.json', 'w') as f:
                json.dump(data, f, default=str)
        elif format == 'csv':
            import csv
            with open('articles_export.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'title', 'content', 'pub_date', 'source_url', 'category'])
                for article in articles:
                    writer.writerow([article.id, article.title, article.content, article.pub_date, article.source_url, article.category])
        else:
            raise ValueError("Unsupported export format")
        
        print(f"Data exported to articles_export.{format}")
    finally:
        session.close()

# Usage:
# export_data('json')  # or export_data('csv')
