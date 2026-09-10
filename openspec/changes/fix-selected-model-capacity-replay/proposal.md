## Why

Selected-model capacity failures still escape through SSE and sequenced WebSocket streams. Earlier retries also leave permission to retry unrelated failures indefinitely.

## What Changes

- Buffer output-free lifecycle preludes until delivery is safe.
- Retry selected-model capacity terminals before forwarding them, preserving output, billing and account-ownership guards.
- Classify upstream identities before downstream rewriting and scope unlimited retries to the current capacity error.
- Publish a corrected container image for the infrastructure release.

## Capabilities

### Modified Capabilities
- `responses-api-compat`: safe selected-model capacity retry across stream transports.

## Impact

Streaming, direct WebSocket and HTTP bridge retry handling. No configuration or schema changes.
