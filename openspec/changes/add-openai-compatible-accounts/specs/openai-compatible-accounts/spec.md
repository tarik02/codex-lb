### Requirement: OpenAI-compatible account creation

The dashboard SHALL allow operators to add an OpenAI-compatible account using a display name, provider base URL, API key, and optional model prefix.

#### Scenario: Account stores provider credentials

- **WHEN** an operator creates an OpenAI-compatible account
- **THEN** the service stores the provider base URL and encrypted API key
- **AND** stores the configured model prefix for public model namespacing

### Requirement: Provider model discovery

The proxy SHALL merge active OpenAI-compatible account models into public model discovery responses.

#### Scenario: Provider exposes Codex catalog

- **GIVEN** an active OpenAI-compatible account
- **AND** the provider exposes `/backend-api/codex/models`
- **WHEN** a client requests `/backend-api/codex/models`
- **THEN** the response includes provider catalog entries using the account model prefix
- **AND** preserves provider metadata such as context windows, reasoning levels, and service tiers

#### Scenario: Provider exposes only OpenAI models

- **GIVEN** an active OpenAI-compatible account
- **AND** the provider exposes `/v1/models`
- **WHEN** a client requests model discovery
- **THEN** the response includes provider models using the account model prefix
- **AND** supplies conservative default Codex metadata for providers without a Codex catalog

### Requirement: Provider request routing

The proxy SHALL route prefixed OpenAI-compatible model requests to the matching provider account.

#### Scenario: Prefixed model request

- **GIVEN** an active OpenAI-compatible account with model prefix `external`
- **AND** the provider advertises upstream model `model-a`
- **WHEN** a client requests `external/model-a`
- **THEN** the proxy sends `model-a` to that provider using the account API key
- **AND** preserves request controls such as `service_tier` for the provider to interpret
