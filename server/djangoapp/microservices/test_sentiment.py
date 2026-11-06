import unittest
from app import app


class SentimentTests(unittest.TestCase):
    def test_fantastic_services_is_positive(self):
        self.assertEqual(app.test_client().get('/analyze/Fantastic%20services').json['sentiment'], 'positive')

    def test_negative_review(self):
        self.assertEqual(app.test_client().get('/analyze/Terrible%20awful%20service').json['sentiment'], 'negative')

    def test_neutral_review(self):
        self.assertEqual(app.test_client().get('/analyze/The%20car%20is%20blue').json['sentiment'], 'neutral')
