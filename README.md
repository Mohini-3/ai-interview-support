# AI-Assisted Technical Interview Companion

## Quick start

1. Create a virtual environment and install dependencies.
2. Run the Flask app.
3. Open the dashboard in your browser.

## Project layout
- app.py: Flask entrypoint
- app/: application package (routes, models, services)
- app/templates/: HTML templates
- app/static/: CSS styles
- interviews.db: SQLite database (auto-generated)

## Notes
- Summary generation is rule-based by default.
- Export produces a JSON report per interview.

## LLM Summary (Hugging Face)

Use a `.env` file (recommended) or set environment variables before starting the app:

- `HF_API_TOKEN`: Your Hugging Face access token
- `HF_MODEL` (optional): Model id (default: `mistralai/Mistral-7B-Instruct-v0.2`)
- `LLM_ENABLED` (optional): `true` to enable LLM summaries
- `HF_TIMEOUT` (optional): Request timeout seconds (default: 30)

Create `.env` from the template:

- Copy `.env.example` to `.env`
- Fill in `HF_API_TOKEN`

Example (PowerShell):

- `setx HF_API_TOKEN "<your_token>"`
- `setx LLM_ENABLED "true"`

Restart your terminal and run the app. The summary endpoint will use the LLM when enabled.

## Future Scopes
- Authentication for the interviewer for Data Security