from openai import OpenAI

from app.config import OPENAI_API_KEY, MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY)


def structured_call(prompt: str, schema, model: str = MODEL_NAME):
    """Run the model and return a validated Pydantic object.

    Uses the OpenAI Responses API structured-output parsing so the model
    is forced to return JSON that matches `schema`. This replaces the
    fragile `json.loads(...)` + bare `except` pattern from the original guide.

    If your installed openai SDK uses a different signature for structured
    parsing, this is the ONLY place you need to adjust it.
    """
    response = client.responses.parse(
        model=model,
        input=prompt,
        text_format=schema,
    )
    return response.output_parsed
