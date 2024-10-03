import argparse
import json
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.api import Api, ApiException
from src.utils import printyellow, printred


# Helper functions
def str_to_bool(value):
    return value.lower() in ['true', '1', 'yes']


def truncate_text(text, max_length=500):
    return text if len(text) <= max_length else f'{text[:max_length]}...'


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def load_config():
    parser = argparse.ArgumentParser(description="Google Maps Data Scraper CLI")
    parser.add_argument('--api-key', default=os.getenv('API_KEY', ''), help='API Key (optional)')
    parser.add_argument('--queries', default=os.getenv('QUERIES', 'Barbershop in Montreal'),
                        help='Queries, separated by commas')
    parser.add_argument('--country', default=os.getenv('COUNTRY', None), help='Country')
    parser.add_argument('--business-type', default=os.getenv('BUSINESS_TYPE', ''), help='Business Type')
    parser.add_argument('--max-cities', default=os.getenv('MAX_CITIES', None), help='Max Cities')
    parser.add_argument('--randomize-cities', type=str_to_bool,
                        default=str_to_bool(os.getenv('RANDOMIZE_CITIES', 'True')),
                        help='Randomize Cities')
    parser.add_argument('--enable-reviews-extraction', type=str_to_bool,
                        default=str_to_bool(os.getenv('ENABLE_REVIEWS_EXTRACTION', 'False')),
                        help='Enable Reviews Extraction')
    parser.add_argument('--max-reviews', type=int, default=int(os.getenv('MAX_REVIEWS', 20)), help='Max Reviews')
    parser.add_argument('--reviews-sort', default=os.getenv('REVIEWS_SORT', 'newest'), help='Reviews Sort')
    parser.add_argument('--lang', default=os.getenv('LANG', None), help='Language')
    parser.add_argument('--max-results', default=os.getenv('MAX_RESULTS', None), help='Max Results')
    parser.add_argument('--coordinates', default=os.getenv('COORDINATES', ''), help='Coordinates')
    parser.add_argument('--zoom-level', type=int, default=int(os.getenv('ZOOM_LEVEL', 14)), help='Zoom Level')

    return parser.parse_args()


args = load_config()

# Postgres connection details
PG_USER = 'postgres'
PG_PASSWORD = 'password'
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB = 'postgres'

# Database configuration
DB_URI = os.getenv('DB_URI', f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")
engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# Define ScrapedData table
class ScrapedData(Base):
    __tablename__ = 'scraped_data'
    id = Column(Integer, primary_key=True)
    query = Column(String)
    results = Column(JSON)


# Ensure the table exists
printyellow("Checking if the 'scraped_data' table exists and creating if necessary...")
Base.metadata.create_all(engine)
printyellow("'scraped_data' table is ready.")


def insert_data(query, results_data):
    with session_scope() as session:
        scraped_data = ScrapedData(query=query, results=results_data)
        session.add(scraped_data)
        printyellow(f"Inserted data for query: {query}")


# API client instance
api = Api()

try:
    data = {
        'queries': args.queries.split(','),
        'country': args.country,
        'business_type': args.business_type,
        'max_cities': args.max_cities,
        'randomize_cities': args.randomize_cities,
        'api_key': args.api_key,
        'enable_reviews_extraction': args.enable_reviews_extraction,
        'max_reviews': args.max_reviews,
        'reviews_sort': args.reviews_sort,
        'lang': args.lang,
        'max_results': args.max_results,
        'coordinates': args.coordinates,
        'zoom_level': args.zoom_level,
    }

    # Create task and get results
    task_list = api.create_task(data, scraper_name='google_maps_scraper')
    task = task_list[0] if isinstance(task_list, list) and task_list else task_list

    task = api.get_task(task['id'])
    # printyellow(f'Fetched task: {task}')

    results = api.get_task_results(task['id'])
    printyellow(f'Fetched task results (truncated): {truncate_text(json.dumps(results, indent=4))}')

    # Insert results into DB
    insert_data(', '.join(args.queries.split(',')), results)

    # Optionally download and store JSON
    results_bytes, filename = api.download_task_results(task['id'], data_format='json')
    printyellow(f'Downloaded results: {filename}')

    api.abort_task(task['id'])
    printyellow(f'Aborted task: {task["id"]}')

    api.delete_task(task['id'])
    printyellow(f'Deleted task: {task["id"]}')

except ApiException as e:
    printred(f"API error: {e}")
except Exception as e:
    printred(f"Unexpected error: {e}")
