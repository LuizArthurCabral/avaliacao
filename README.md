# Sistema de Mensagens Distribuído

Três containers Flask (`app1`, `app2`, `app3`) que trocam mensagens entre si
por uma rede bridge e guardam seus logs em um volume compartilhado.

## Estrutura

```
/avaliacao
├── app/
│   ├── app.py            # Código principal
│   ├── requirements.txt  # Dependências
│   └── Dockerfile        # Dockerfile da aplicação
├── docker-compose.yml    # Arquivo compose
├── test.sh               # Script de teste
└── README.md             # Instruções
```

## Como funciona

- Cada instância tem `NODE_ID` e `PEERS` definidos no `docker-compose.yml`.
- `POST /send` salva a mensagem no log do próprio container
  (`/app/data/<NODE_ID>.jsonl`) e envia uma cópia para os outros dois via
  `POST /replicate`, usando o nome do serviço como host.
- `/replicate` apenas salva (não repassa, evitando loops) e ignora IDs repetidos.
- `GET /verify` compara as mensagens do container com as dos peers.

## Componentes Docker

| Item | Detalhe |
|---|---|
| Serviços | `app1` (5001), `app2` (5002), `app3` (5003) |
| Volume | `shared_data` montado em `/app/data` |
| Rede | `msg_network` (bridge personalizada) |

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/send` | Recebe JSON, salva e replica para os peers |
| POST | `/replicate` | Uso interno: recebe cópia de outro container |
| GET | `/messages` | Lista as mensagens do container |
| GET | `/verify` | Verifica se os peers têm as mesmas mensagens |

## Como executar

```bash
docker compose up -d --build
```

## Exemplo de uso

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"hello"}' http://localhost:5001/send

curl http://localhost:5002/messages
curl http://localhost:5001/verify
```

Ver os logs de cada container no volume:

```bash
docker compose exec app1 ls /app/data
```

## Testes

```bash
chmod +x test.sh
./test.sh
```

O script sobe os containers, envia uma mensagem pelo `app1`, confere que ela
aparece nos três containers e valida o `/verify`.

## Encerrar

```bash
docker compose down        # mantém o volume
docker compose down -v     # remove também o volume
```

## Limitações

- Usa o servidor de desenvolvimento do Flask (adequado para esta atividade;
  em produção usaria gunicorn).
- Se um peer estiver fora do ar, a cópia não é reenviada depois. O `/verify`
  mostra a divergência.
