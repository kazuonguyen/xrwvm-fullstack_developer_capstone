"""HTTP contract and access-control tests; external microservices are mocked here."""
import json
from unittest.mock import patch
import requests
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import CarMake, CarModel


class APITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('driver', 'driver@example.com', 'Driver-Test-2026!', first_name='Demo', last_name='Driver')
        make = CarMake.objects.create(name='Toyota', description='Passenger vehicles')
        self.car = CarModel.objects.create(car_make=make, name='Camry', year=2023, type='Sedan')

    def post(self, path, data):
        return self.client.post('/djangoapp/' + path, json.dumps(data), content_type='application/json')

    def test_login_logout_and_session(self):
        self.assertFalse(self.client.get('/djangoapp/session').json()['authenticated'])
        response = self.post('login', {'userName':'driver', 'password':'Driver-Test-2026!'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.get('/djangoapp/session').json()['authenticated'])
        self.assertEqual(self.post('logout', {}).status_code, 200)
        self.assertFalse(self.client.get('/djangoapp/session').json()['authenticated'])

    def test_invalid_login(self):
        self.assertEqual(self.post('login', {'userName':'driver','password':'incorrect'}).status_code, 401)

    def test_registration_and_duplicate(self):
        data = {'username':'newdriver','first_name':'New','last_name':'Driver','email':'new@example.com','password':'Fresh-Driver-2026!'}
        self.assertEqual(self.post('register', data).status_code, 201)
        self.assertEqual(self.post('register', data).status_code, 409)

    def test_registration_requires_five_fields(self):
        self.assertEqual(self.post('register', {'username':'incomplete'}).status_code, 400)

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/djangoapp/login', '{}', content_type='application/json').status_code, 403)
        token = client.get('/djangoapp/session').json()['csrfToken']
        response = client.post('/djangoapp/login', json.dumps({'userName':'driver','password':'Driver-Test-2026!'}), content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_car_catalog_contains_makes_and_models(self):
        data = self.client.get('/djangoapp/get_cars').json()
        self.assertEqual(data['CarMakes'][0]['name'], 'Toyota')
        self.assertEqual(data['CarModels'][0]['CarModel'], 'Camry')

    @patch('djangoapp.views.get_request', return_value=[{'id':8,'state':'Kansas'}])
    def test_state_proxy(self, get):
        response = self.client.get('/djangoapp/get_dealers/Kansas')
        self.assertEqual(response.json()['dealers'][0]['state'], 'Kansas')
        get.assert_called_once_with('fetchDealers/Kansas')

    @patch('djangoapp.views.get_request', return_value=[])
    def test_missing_dealer(self, _get):
        self.assertEqual(self.client.get('/djangoapp/dealer/999').status_code, 404)

    @patch('djangoapp.views.analyze_review_sentiments', return_value={'sentiment':'positive'})
    @patch('djangoapp.views.get_request', return_value=[{'id':1,'review':'Fantastic services'}])
    def test_reviews_include_sentiment(self, _get, _sentiment):
        self.assertEqual(self.client.get('/djangoapp/reviews/dealer/8').json()['reviews'][0]['sentiment'], 'positive')

    def test_anonymous_review_is_rejected(self):
        self.assertEqual(self.post('add_review', {}).status_code, 401)

    @patch('djangoapp.views.post_review', return_value={'id':51})
    @patch('djangoapp.views.analyze_review_sentiments', return_value={'sentiment':'positive'})
    @patch('djangoapp.views.get_request', return_value=[{'id':8}])
    def test_review_author_comes_from_session(self, _get, _sentiment, post):
        self.client.force_login(self.user)
        response = self.post('add_review', {'name':'Forged Author','dealership':8,'review':'Fantastic services','purchase_date':'2026-01-01','car_model_id':self.car.pk,'car_year':2023})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_args.args[0]['name'], 'Demo Driver')
        self.assertEqual(post.call_args.args[0]['car_make'], 'Toyota')

    @patch('djangoapp.views.get_request', side_effect=requests.Timeout())
    def test_microservice_failure_returns_503(self, _get):
        self.assertEqual(self.client.get('/djangoapp/get_dealers').status_code, 503)

    def test_malformed_json_returns_400(self):
        response = self.client.post('/djangoapp/login', '{invalid', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_logout_is_post_only(self):
        self.assertEqual(self.client.get('/djangoapp/logout').status_code, 405)

    def test_static_pages(self):
        self.assertContains(self.client.get('/about/'), 'Meet our team')
        self.assertContains(self.client.get('/contact/'), 'Customer support')
