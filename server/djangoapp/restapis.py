"""HTTP clients for the Node/Mongo API and Flask sentiment service."""
from urllib.parse import quote
import os
import requests

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:3030').rstrip('/')
SENTIMENT_URL = os.environ.get('SENTIMENT_URL', 'http://127.0.0.1:5050').rstrip('/')


def get_request(endpoint):
    response = requests.get(f'{BACKEND_URL}/{endpoint.lstrip("/")}', timeout=15)
    response.raise_for_status()
    return response.json()


def analyze_review_sentiments(text):
    response = requests.get(f'{SENTIMENT_URL}/analyze/{quote(text, safe="")}', timeout=15)
    response.raise_for_status()
    return response.json()


def post_review(data):
    response = requests.post(f'{BACKEND_URL}/insert_review', json=data, timeout=15)
    response.raise_for_status()
    return response.json()
