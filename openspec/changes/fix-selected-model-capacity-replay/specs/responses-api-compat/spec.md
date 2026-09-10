## ADDED Requirements

### Requirement: Selected-model capacity retries preserve stream safety

The proxy MUST retry an output-free selected-model capacity failure without a retry-count limit while the consumer remains attached. It MUST buffer SSE lifecycle-only preludes and sequenced direct WebSocket lifecycle-only preludes before downstream delivery. It MUST NOT replay after actual output, billed output, or a delivered numeric sequence. Required account ownership MUST remain intact. Quota and rate-limit error codes MUST take precedence over capacity wording.

#### Scenario: Repeated accepted capacity failures
- **WHEN** successive upstream attempts emit only lifecycle preludes followed by selected-model capacity errors
- **THEN** the proxy retries without exposing failed lifecycles
- **AND** classifiers compare the original upstream response identity before downstream ID rewriting

#### Scenario: Unrelated failure after capacity
- **WHEN** a capacity retry encounters a different error or transport failure
- **THEN** the existing bounded retry and deadline rules apply to that failure

#### Scenario: Concurrent WebSocket submit during capacity delay
- **WHEN** the reader decides to replay a capacity failure
- **THEN** it establishes reconnect ownership before awaiting the retry delay
