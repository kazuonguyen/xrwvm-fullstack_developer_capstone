"""Session authentication and dealership API endpoints."""
import json
from functools import wraps
from datetime import date
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_GET, require_POST
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review


def json_body(request):
    data = json.loads(request.body)
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    return data


def api_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except (ValueError, KeyError, TypeError, ValidationError, CarModel.DoesNotExist) as error:
            return JsonResponse({'status': 400, 'message': str(error)}, status=400)
        except requests.RequestException:
            return JsonResponse({'status': 503, 'message': 'The dealership service is temporarily unavailable.'}, status=503)
    return wrapped


def user_data(user):
    return {'userName': user.username, 'firstname': user.first_name, 'lastname': user.last_name}


@require_GET
def session_info(request):
    data = {'authenticated': request.user.is_authenticated, 'csrfToken': get_token(request)}
    if request.user.is_authenticated:
        data.update(user_data(request.user))
    return JsonResponse(data)


@require_POST
@api_errors
def login_user(request):
    data = json_body(request)
    user = authenticate(request, username=data.get('userName', ''), password=data.get('password', ''))
    if user is None:
        return JsonResponse({'status': 401, 'message': 'Invalid username or password.'}, status=401)
    login(request, user)
    return JsonResponse({'status': 200, 'statusMessage': 'Authenticated', **user_data(user), 'csrfToken': get_token(request)})


@require_POST
def logout_request(request):
    logout(request)
    return JsonResponse({'status': 200, 'message': 'Logged out successfully.'})


@require_POST
@api_errors
def registration(request):
    data = json_body(request)
    for key in ('username', 'first_name', 'last_name', 'email', 'password'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError('All five fields are required.')
    validate_email(data['email'])
    if len(data['username']) > 150:
        raise ValueError('Username is too long.')
    validate_password(data['password'])
    try:
        with transaction.atomic():
            user = User.objects.create_user(data['username'].strip(), data['email'].strip(), data['password'],
                first_name=data['first_name'].strip(), last_name=data['last_name'].strip())
    except IntegrityError:
        return JsonResponse({'status': 409, 'message': 'Username already exists.'}, status=409)
    login(request, user)
    return JsonResponse({'status': 201, **user_data(user), 'csrfToken': get_token(request)}, status=201)


@require_GET
@api_errors
def get_dealerships(request, state=None):
    endpoint = 'fetchDealers' if not state or state == 'All' else f'fetchDealers/{requests.utils.quote(state, safe="")}'
    return JsonResponse({'status': 200, 'dealers': get_request(endpoint)})


@require_GET
@api_errors
def get_dealer_details(request, dealer_id):
    dealer = get_request(f'fetchDealer/{dealer_id}')
    if not dealer:
        return JsonResponse({'status': 404, 'message': 'Dealer not found.'}, status=404)
    return JsonResponse({'status': 200, 'dealer': dealer})


@require_GET
@api_errors
def get_dealer_reviews(request, dealer_id):
    reviews = get_request(f'fetchReviews/dealer/{dealer_id}')
    for review in reviews:
        review['sentiment'] = analyze_review_sentiments(review['review'])['sentiment']
    return JsonResponse({'status': 200, 'reviews': reviews})


@require_GET
def get_cars(request):
    models = [{'id': car.id, 'CarMake': car.car_make.name, 'CarModel': car.name,
               'type': car.type, 'year': car.year} for car in CarModel.objects.select_related('car_make').order_by('car_make__name', 'name')]
    return JsonResponse({'status': 200, 'CarMakes': list(CarMake.objects.order_by('name').values('id', 'name', 'description')), 'CarModels': models})


@require_POST
@api_errors
def add_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 401, 'message': 'Log in to review a dealer.'}, status=401)
    data = json_body(request)
    text = data.get('review', '').strip()
    if not 5 <= len(text) <= 5000:
        raise ValueError('Review must contain 5–5000 characters.')
    dealer_id = int(data['dealership'])
    if not get_request(f'fetchDealer/{dealer_id}'):
        return JsonResponse({'status': 404, 'message': 'Dealer not found.'}, status=404)
    model = CarModel.objects.select_related('car_make').get(pk=int(data['car_model_id']))
    purchase_date = date.fromisoformat(data['purchase_date'])
    year = int(data['car_year'])
    if not 2015 <= year <= 2030 or purchase_date > date.today():
        raise ValueError('Check the car year and purchase date.')
    saved = post_review({'name': request.user.get_full_name() or request.user.username,
        'dealership': dealer_id, 'review': text, 'purchase': True,
        'purchase_date': purchase_date.isoformat(), 'car_make': model.car_make.name,
        'car_model': model.name, 'car_year': year})
    saved['sentiment'] = analyze_review_sentiments(text)['sentiment']
    return JsonResponse({'status': 200, 'review': saved})


@require_GET
@api_errors
def analyze_review(request, text):
    return JsonResponse(analyze_review_sentiments(text))
