# LLM Clients - Consistency Improvements

## Completed

### 1. `validate_model()` now called in `get_llm()`
- All three clients (OpenAI, Anthropic, Google) call `validate_model()` at the start of `get_llm()`
- Issues a warning (not error) for unknown models — allows new/custom models to work

### 2. Unified `api_key` parameter
- All clients now accept `api_key` kwarg and map it to provider-specific keys:
  - OpenAI/xAI/DeepSeek/DashScope: passed directly as `api_key`
  - Anthropic: mapped to `anthropic_api_key`
  - Google: mapped to `google_api_key` (still accepts `google_api_key` directly too)

### 3. `base_url` handling clarified
- OpenAI client: uses `base_url` as fallback when provider doesn't have a built-in URL
- Anthropic client: maps `base_url` to `anthropic_api_url`
- Google client: `base_url` accepted but unused (Google doesn't support custom endpoints)

### 4. validators.py synced with all providers
- Added deepseek and dashscope model lists
- Updated docstring for validate_model()

## Remaining

- Monitor new model releases and update VALID_MODELS accordingly
