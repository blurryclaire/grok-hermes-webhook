# grok-hermes-webhook

[![tests](https://github.com/deedade/grok-hermes-webhook/actions/workflows/ci.yml/badge.svg)](https://github.com/deedade/grok-hermes-webhook/actions/workflows/ci.yml)

Hand Grok Bot tasks to local Hermes — signed webhook, non-empty task, local 202 stub.

Minimal **Grok Bot ↔ Hermes** webhook contract: require a non-empty `payload.task`, verify **HMAC-SHA256** over the raw body, and return **202 accepted** from a tiny local receiver stub — with **zero real secrets** in the tree. It is not an xAI API client.

## Why

Empty tasks still get accepted, signatures are checked only after JSON parse, or a secret lands in git. This localhost stub is the small reference that closes those gaps. v0.1 is stdlib under MIT. It acknowledges a signed task. It does not run the job.

Other agents can reuse the HMAC, non-empty-task, and 202 pattern. This tree is the **Grok Bot ↔ Hermes** reference, not a multi-runtime product.

## Use cases

- Turn a strategy or draft into a local Hermes job — an API call, an IoT action, or a cron-style task — without committing secrets.
- Refuse an empty or missing task before any work starts.
- Refuse a bad signature before the body is parsed as JSON.

## Workflow

1. Grok Bot turns a strategy or draft into a task. The task string must be non-empty.
2. A client posts that task as a signed webhook. The signature is `HMAC-SHA256` over the raw body. `WEBHOOK_SECRET` stays in the environment.
3. The local Hermes receiver returns **202 accepted** (`status=accepted`, `route=grok-bot-task`) and does not wait for the job to finish.
4. After the async work, status comes back as a four-part report.

**v0.1 stops at step 3.** The receiver checks the signature and the task, then returns 202. It does not enqueue the job, run it, or emit the four-part report. **202 means accepted for async work, not completed.**

Chat questions and answers do not use this webhook. They go to a separate completions API: `POST /v1/chat/completions` with `Authorization: Bearer $API_SERVER_KEY`. Document environment **names** only — never real keys.

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

## Pitfalls

- Empty task, or a template placeholder that was never replaced.
- Parsing JSON **before** verifying HMAC on the raw body.
- Committing `WEBHOOK_SECRET`, API keys, ngrok URLs, or chat group ids.
- Treating **202**, or a short ack, as the finished result. The four-part report is not this stub's response.
- No idempotency or replay window in v0.1.

## Layout

```
src/grok_hermes_webhook/   # validate, hmac_verify, receiver stub
examples/                  # valid + empty-task payloads
tests/                     # unit tests
docs/contract.md
.github/workflows/ci.yml   # pytest on push and pull_request
```

## What v0.1 does **not** include

- Real ngrok / tunnel URLs, API keys, or chat group ids
- Production queue, retries, replay window, or the four-part status report
- Scrapers or other product repos

## License

MIT
