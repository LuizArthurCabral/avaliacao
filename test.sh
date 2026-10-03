#!/bin/bash
set -e

docker compose down -v
docker compose up -d --build

echo "Aguardando os containers..."
for port in 5001 5002 5003; do
  for i in $(seq 1 20); do
    curl -sf http://localhost:$port/messages > /dev/null && break
    sleep 1
  done
done

echo "Enviando mensagem pelo app1..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"message":"hello"}' http://localhost:5001/send
echo

for port in 5001 5002 5003; do
  echo "Mensagens em localhost:$port"
  curl -s http://localhost:$port/messages
  echo
done

echo "Verificação de replicação (app1):"
VERIFY=$(curl -s http://localhost:5001/verify)
echo "$VERIFY"

echo "Logs no volume:"
docker compose exec -T app1 ls /app/data

for port in 5001 5002 5003; do
  if ! curl -s http://localhost:$port/messages | grep -q "hello"; then
    echo "FALHA: mensagem não chegou em localhost:$port."
    exit 1
  fi
done

if echo "$VERIFY" | grep -qE '"ok": *false'; then
  echo "FALHA: /verify reportou inconsistência."
  exit 1
fi

echo "SUCESSO: mensagem replicada nos três containers."