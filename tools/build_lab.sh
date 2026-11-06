#!/usr/bin/env bash
set -euo pipefail
cd /home/project
if [ ! -d cars-capstone/.git ]; then
  git clone https://github.com/kazuonguyen/xrwvm-fullstack_developer_capstone.git cars-capstone
fi
cd cars-capstone
git pull --ff-only
mkdir -p evidence
NAMESPACE=sn-labs-hungtvt2222
REGISTRY=us.icr.io/$NAMESPACE
docker network inspect cars-network >/dev/null 2>&1 || docker network create cars-network
# Each image is built from the completed project, with complete build/push logs.
docker build --progress=plain -t "$REGISTRY/cars-api:capstone" server/database 2>&1 | tee evidence/build-api.txt
docker push "$REGISTRY/cars-api:capstone" 2>&1 | tee evidence/push-api.txt
docker build --progress=plain -t "$REGISTRY/cars-sentiment:capstone" server/djangoapp/microservices 2>&1 | tee evidence/build-sentiment.txt
docker push "$REGISTRY/cars-sentiment:capstone" 2>&1 | tee evidence/push-sentiment.txt
docker build --progress=plain -t "$REGISTRY/dealership:capstone" server 2>&1 | tee evidence/build-dealership.txt
docker push "$REGISTRY/dealership:capstone" 2>&1 | tee evidence/push-dealership.txt
# Local lab services are separate from the subsequent Kubernetes deployment.
docker volume create cars-mongo-data >/dev/null
docker run -d --name cars-mongo --network cars-network -v cars-mongo-data:/data/db mongo:7.0
docker run -d --name cars-api --network cars-network -e MONGO_URL=mongodb://cars-mongo:27017/dealershipsDB -p 127.0.0.1:3030:3030 "$REGISTRY/cars-api:capstone"
docker run -d --name cars-sentiment --network cars-network -p 127.0.0.1:5050:5000 "$REGISTRY/cars-sentiment:capstone"
docker run -d --name cars-dev --network cars-network --env-file /tmp/cars.env -e BACKEND_URL=http://cars-api:3030 -e SENTIMENT_URL=http://cars-sentiment:5000 -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.cognitiveclass.ai -p 8000:8000 "$REGISTRY/dealership:capstone" python manage.py runserver 0.0.0.0:8000 --noreload
for attempt in $(seq 1 90); do
  if curl -fsS http://127.0.0.1:8000/djangoapp/get_dealers >/dev/null; then break; fi
  sleep 2
done
curl -fsS http://127.0.0.1:8000/djangoapp/get_dealers >/dev/null
docker logs cars-dev > evidence/django_server.txt 2>&1
printf 'Full development stack is ready on port 8000.\n'
