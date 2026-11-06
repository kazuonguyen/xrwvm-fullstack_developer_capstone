"""Flask microservice using the bundled NLTK VADER sentiment lexicon."""
from pathlib import Path
from flask import Flask, jsonify
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
nltk.data.path.insert(0, str(Path(__file__).resolve().parent))
app = Flask(__name__)
sia = SentimentIntensityAnalyzer()


@app.get('/')
def home():
    return jsonify(service='Sentiment Analyzer', model='NLTK VADER')


@app.get('/analyze/<path:input_txt>')
def analyze_sentiment(input_txt):
    scores = sia.polarity_scores(input_txt)
    sentiment = 'positive' if scores['compound'] >= 0.05 else 'negative' if scores['compound'] <= -0.05 else 'neutral'
    return jsonify(sentiment=sentiment, scores=scores)
