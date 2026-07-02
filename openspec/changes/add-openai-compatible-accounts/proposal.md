# Add OpenAI-Compatible Accounts

## Why

Operators may need to route traffic to API-key-backed providers that expose OpenAI-compatible `/v1` endpoints. The current account pool is ChatGPT OAuth-specific, so these providers cannot be configured, discovered, or routed from the dashboard.

## What Changes

- Add an OpenAI-compatible account type with provider base URL, API key, and model prefix configuration.
- Merge provider model discovery into `/v1/models` and `/backend-api/codex/models`.
- Route requests for prefixed provider models to the matching OpenAI-compatible account after codex-lb API-key validation.
- Preserve provider Codex model catalog metadata when the provider exposes `/backend-api/codex/models`.

## Impact

- Existing ChatGPT OAuth account behavior is unchanged.
- API-key-backed accounts are excluded from OAuth refresh and ChatGPT usage refresh jobs.
