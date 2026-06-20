# AarthSaathi Financial Orchestrator API

This API provides secure, authenticated access to the AarthSaathi financial advice orchestration system.

## Features

- **Scoped Authentication**: Different API keys can have different permissions
- **Component-Level Access**: Access to individual agents/engines or the full orchestrator
- **Audit Ready**: All access can be logged and monitored
- **Backward Compatible**: Supports legacy GROQ_API_KEY authentication

## Authentication

The API uses API key-based authentication with scoped permissions.

### Getting Started

1. Set your `API_KEY_PEPPER` in the `.env` file (generate a random string)
2. Run the admin key creation script:
   ```bash
   python create_admin_key.py
   ```
3. Use the generated API key in the `X-Api-Key` header or as a Bearer token

### Scopes Available

- `education_agent:invoke` - Access to the education agent
- `budget_calculation:invoke` - Access to budget calculation engine
- `income_classification:invoke` - Access to income classification engine
- `readiness_scoring:invoke` - Access to readiness scoring engine
- `guardrails_filter:invoke` - Access to guardrails filtering layer
- `orchestrator:full` - Access to the full orchestrator pipeline
- `status:read` - Access to health and status endpoints

## API Endpoints

All endpoints are prefixed with `/api/v1`

### Health & Status
- `GET /` - Service information (requires `status:read`)
- `GET /health` - Health check (no authentication required)

### Individual Components
- `POST /agents/education` - Get financial concept explanation (requires `education_agent:invoke`)
- `POST /engines/budget` - Calculate budget (requires `budget_calculation:invoke`)
- `POST /engines/income-classification` - Classify income (requires `income_classification:invoke`)
- `POST /engines/readiness-scoring` - Calculate readiness score (requires `readiness_scoring:invoke`)
- `POST /layers/guardrails` - Run guardrails check (requires `guardrails_filter:invoke`)

### Orchestrator
- `POST /orchestrator/run` - Run full financial pipeline (requires `orchestrator:full`)

## Usage Example

```bash
# Get an education explanation
curl -X POST "http://localhost:8000/api/v1/agents/education" \
  -H "X-Api-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "concept": "emergency fund",
    "readiness": "stabilize_first",
    "income_type": "fixed",
    "language": "english"
  }'

# Run the full orchestrator
curl -X POST "http://localhost:8000/api/v1/orchestrator/run" \
  -H "X-Api-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "income": {"monthly_fixed": 35000},
    "obligations": {"rent": 8000, "groceries": 6000, "transport": 4000, "medical": 4000, "education": 3500},
    "emergency_data": {"current_savings": 0, "monthly_emi_total": 0}
  }'
```

## Security Notes

- Never commit your `.env` file with real API keys to version control
- Use different API keys for different clients/services with appropriate scopes
- Rotate API keys periodically
- Monitor API usage logs for abnormal activity