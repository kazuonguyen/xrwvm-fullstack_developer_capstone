#!/usr/bin/env bash
set -euo pipefail
cd /home/project/cars-capstone
# Runtime credentials live outside Git and are never printed.
kubectl create secret generic cars-runtime --from-env-file=/tmp/cars.env
kubectl apply -f server/deployment.yaml 2>&1 | tee evidence/kubernetes-apply.txt
for name in cars-db cars-api cars-sentiment dealership; do
  kubectl rollout status deployment/$name --timeout=300s 2>&1 | tee -a evidence/kubernetes-rollouts.txt
done
kubectl get deployment,pods,services,pvc -l app=dealership 2>&1 | tee evidence/kubernetes-main.txt
