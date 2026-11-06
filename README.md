# Cars Dealership — Full Stack Capstone

A responsive dealership review application built with React, Django, Node.js,
MongoDB, SQLite, and a Flask/NLTK sentiment microservice. Based on IBM's
xrwvm-fullstack_developer_capstone starter.

## Services

- Django serves the built React UI, session authentication, car catalog and API proxy.
- Express stores dealerships and customer reviews in MongoDB. Initial seed data
  is inserted only when missing, preserving reviews across service restarts.
- Flask runs the bundled NLTK VADER model and returns positive/neutral/negative sentiment.
- SQLite stores users and the CarMake/CarModel catalog.

## Run with Docker Compose

Set `DJANGO_SECRET_KEY`, `DEMO_ADMIN_PASSWORD`, and `DEMO_USER_PASSWORD` in
your environment, then run `docker compose -f server/compose.yml up --build`.
The UI is served on http://127.0.0.1:8000. The configured demonstration accounts
are `root` (Django admin) and `demo_user` (customer). Passwords are not stored in source.

## Validation

```bash
cd server/frontend && npm ci && npm run build
cd ..
python manage.py check
python manage.py test djangoapp -v 2
cd djangoapp/microservices
python -m unittest test_sentiment -v
```

The CI workflow builds React, tests Django authentication/API contracts, tests
real NLTK inference, exercises Express against a real MongoDB service, and builds
the production Django image. HTTP microservices are mocked only in Django's
isolated unit tests; submission cURL evidence must come from a running full stack.

## Static pages and photographs

About Us and Contact Us use shared CSS and responsive navigation. Team profiles
and contact details are illustrative. Team photographs are from Unsplash:
photo-1500648767791-00dcc994a43e, photo-1494790108377-be9c29b29330,
and photo-1517841905240-472988babdf9, used under https://unsplash.com/license.

## References

- Starter: https://github.com/ibm-developer-skills-network/xrwvm-fullstack_developer_capstone
- Django tests: https://docs.djangoproject.com/en/5.2/topics/testing/tools/
- IBM container lab: https://cf-courses-data.static.labs.skills.network/tjGGlDfSdjazlzEVabUlgA/ContainerizeAndDeploy-Mark-v1.md
