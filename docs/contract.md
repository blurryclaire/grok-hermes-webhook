# Webhook contract (v0.1)

Local receiver contract for the **Grok Bot ↔ Hermes** stub. Chat replies are not this webhook.

## Body

- JSON **object**, max **1 MiB**
- Required: a non-empty task string (after strip), max **8000** chars
- Accepted task keys (first match wins): `task` | `message` | `prompt` | `instruction`
- Optional: `source`, `delivery_id`, `priority`, `context`, `reply_to`

## Signature

- Header: `X-Webhook-Signature` (also accept `X-Hub-Signature-256` / `sha256=<hex>`)
- Algorithm: `HMAC-SHA256(raw_body).hexdigest()`
- Secret: environment variable **`WEBHOOK_SECRET`** (never commit real values)
- Verify with `hmac.compare_digest`
- **Order (fail closed):** read raw bytes → verify signature → parse JSON → schema / non-empty task
- Recommended: add a timestamp + skew window later to limit replay (not required in v0.1 stub)

## Responses

| Status | When |
|--------|------|
| **202** | Accepted: `{"status":"accepted","route":"grok-bot-task","delivery_id":"..."}` |
| **400** | Empty / missing task, or invalid JSON |
| **401** | Missing / invalid signature |
| **404** | Wrong path |
| **413** | Body too large |

**202 means accepted for async work, not completed.** The later four-part status report is outside this stub.

## Chat completions (not this webhook)

Full conversational replies go through an HTTP API such as `/v1/chat/completions` with `Authorization: Bearer $API_SERVER_KEY`. Document only env **names** in this repo — never real keys.

## Pitfalls

- Empty task or unreplaced template placeholders
- No toolset configured on the consumer side
- Treating ack text (“收到”) as the real result
- Treating **202** as job finished
- No idempotency / replay protection
- Parsing JSON **before** verifying HMAC
- Committing secrets, ngrok URLs, or chat group ids
