import json
import os
import re

from groq import Groq

_client: Groq | None = None

MODEL = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY no está definida en .env")
        _client = Groq(api_key=api_key)
    return _client


def call_llm(prompt: str, system: str = "Eres un asistente experto. Responde solo con JSON válido, sin markdown.",
             max_tokens: int = 4096) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


def call_llm_json(prompt: str, system: str = "Eres un asistente experto. Responde solo con JSON válido, sin markdown ni texto adicional.",
                  max_tokens: int = 4096) -> dict:
    """Llama al LLM en modo JSON nativo — garantiza salida JSON válida siempre."""
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


def parse_json(text: str) -> dict:
    text = text.strip()
    # Remover fences de markdown si existen
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Intento de recuperación: buscar el primer { ... } o [ ... ]
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"No se pudo parsear JSON: {e}\nRespuesta recibida:\n{text[:500]}")
