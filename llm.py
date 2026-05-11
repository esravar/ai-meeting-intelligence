from openai import OpenAI, RateLimitError
from config import OPENROUTER_API_KEY
import time

FALLBACK_MODELS = [
    "openrouter/free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-4-31b-it:free",
]


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def ask_llm(context: str, question: str):

    client = get_client()

    prompt = f"""
You are a corporate knowledge assistant.

Answer ONLY using the provided context.

If the answer cannot be found, say:
"I could not find this information in the uploaded documents."

Context:
{context}

Question:
{question}
"""

    last_error = None

    for model in FALLBACK_MODELS:

        try:

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You answer questions using corporate documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
            )

            answer = response.choices[0].message.content

            return {
                "answer": answer,
                "model_used": model,
                "success": True,
            }

        except RateLimitError as e:
            print(f"Rate limited on model: {model}")
            last_error = str(e)

        except Exception as e:
            print(f"Error on model: {model}")
            last_error = str(e)
            time.sleep(1)

    return {
        "answer": f"All fallback models failed.\n\nLast error:\n{last_error}",
        "model_used": None,
        "success": False,
    }