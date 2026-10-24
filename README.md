# grok-hermes-webhook

Minimal **Grok ↔ Hermes** webhook contract: require a non-empty `payload.task`, verify **HMAC-SHA256** over the raw body, and return **202 accepted** from a tiny local receiver stub — with **zero real secrets** in the tree.

## Why

Agent bridges often fail closed on the wrong things (empty tasks, signatures checked after JSON parse, secrets in git). This repo is a small, copyable reference you can run locally.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set WEBHOOK_SECRET
export $(grep -v '^#' .env | xargs)
python -m grok_hermes_webhook.receiver
```

In another shell:

```bash
BODY='{"task":"ping from local stub"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')
curl -sS -X POST "http://127.0.0.1:8650/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIG" \
  -d "$BODY"
```

Expected: HTTP **202** with `status=accepted`, `route=grok-bot-task`.

## Contract (short)

| Item | Rule |
|------|------|
| Task | Required non-empty string (aliases: `task` \| `message` \| `prompt` \| `instruction`) |
| Signature | `HMAC-SHA256(raw_body)` via `X-Webhook-Signature` (or `X-Hub-Signature-256` / `sha256=`) |
| Secret | `WEBHOOK_SECRET` env only |
| Success | **202** — accepted for async work, **not** completed |
| Chat replies | Separate `/v1/chat/completions` + `API_SERVER_KEY` (env name only) |

Full notes: [`docs/contract.md`](docs/contract.md).

## Layout

```
src/grok_hermes_webhook/   # validate, hmac_verify, receiver stub
examples/                  # valid + empty-task payloads
tests/                     # unit tests
docs/contract.md
```

## What v0.1 does **not** include

- Real ngrok / tunnel URLs, API keys, chat group ids
- Production queue, retries, or replay window
- Scrapers or other product repos

## License

MIT
