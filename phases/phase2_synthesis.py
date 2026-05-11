"""
Fase 2: Genera 3 hooks candidatos y selecciona el mejor para TDAH.
Salida: output/phase2_hook.json
"""

import json
import os

from utils.checkpoint import checkpoint_or_run
from utils.groq_client import call_llm_json

SYSTEM = (
    "Eres un experto en comunicación visual y diseño para usuarios con TDAH. "
    "Responde ÚNICAMENTE con JSON válido, sin markdown ni texto adicional."
)

PROMPT_GENERATE = """El PDF trata sobre: "{tema_central}"
Idea central: "{idea_central}"
Palabras clave del documento: {palabras_clave}

Tu tarea: Genera 3 hooks de apertura para un video de 8-15 segundos sobre este tema específico.

REGLAS ESTRICTAS:
- Máximo 8 palabras por hook
- Cada hook DEBE aludir directamente al tema "{tema_central}" o a alguna de sus palabras clave
- PROHIBIDO usar frases genéricas vacías como "Atención", "Ahora", "Descubre", "Mira esto", "¿Sabías?" sin conectarlas al tema
- El hook debe provocar impacto en alguien que NO sabe nada del tema todavía

Ejemplos de hooks MALOS (genéricos, no usar):
- "Atención, ¡ahora!" → no dice nada del tema
- "Descubre algo nuevo" → podría ser de cualquier video
- "¿Puedes enfocarte?" → genérico

Ejemplos de hooks BUENOS (específicos al tema):
- Si el tema es TDAH: "Tu cerebro no falla, compite contra todo"
- Si el tema es diseño: "Un mal diseño le cuesta atención al usuario"
- Si el tema es neurociencia: "Cada imagen activa neuronas que no sabías tener"

Responde ÚNICAMENTE con JSON válido:
{{
  "candidatos": [
    {{"id": 1, "texto": "...", "razon": "cómo se conecta con el tema del PDF"}},
    {{"id": 2, "texto": "...", "razon": "..."}},
    {{"id": 3, "texto": "...", "razon": "..."}}
  ]
}}"""

PROMPT_SELECT = """Eres un psicólogo cognitivo especializado en atención y TDAH.

Se te presentan 3 opciones de hook para un video diseñado para usuarios con TDAH.
El video trata sobre: {idea_central}

CANDIDATOS:
{candidatos}

Evalúa cada hook según:
1. Brevedad (menos palabras = mejor para TDAH)
2. Saliencia emocional inmediata (impacto en <2 segundos)
3. Ausencia de carga cognitiva (no requiere análisis previo)
4. Efecto de novedad o sorpresa

Responde ÚNICAMENTE con JSON válido:
{{
  "seleccionado": {{
    "id": <número>,
    "texto": "<texto exacto del hook>",
    "justificacion_tdah": "..."
  }}
}}"""


def generate_hooks(analysis: dict) -> dict:
    prompt = PROMPT_GENERATE.format(
        tema_central=analysis.get("tema_central", ""),
        idea_central=analysis.get("idea_central", ""),
        palabras_clave=", ".join(analysis.get("palabras_clave", [])),
    )
    return call_llm_json(prompt, system=SYSTEM)


def select_hook(analysis: dict, candidatos: list) -> dict:
    prompt = PROMPT_SELECT.format(
        idea_central=analysis.get("idea_central", ""),
        candidatos=json.dumps(candidatos, ensure_ascii=False, indent=2),
    )
    return call_llm_json(prompt, system=SYSTEM)


def synthesize(analysis: dict) -> dict:
    print("  Generando 3 hooks candidatos...")
    hooks_data = generate_hooks(analysis)
    candidatos = hooks_data.get("candidatos", [])

    print("  Seleccionando el mejor hook para TDAH...")
    selection_data = select_hook(analysis, candidatos)

    return {
        "candidatos": candidatos,
        "seleccionado": selection_data.get("seleccionado", {}),
    }


def run(pdf_path: str, output_dir: str) -> dict:
    analysis_path = os.path.join(output_dir, "phase1_analysis.json")
    checkpoint_path = os.path.join(output_dir, "phase2_hook.json")

    from utils.checkpoint import load_checkpoint
    analysis = load_checkpoint(analysis_path)
    if analysis is None:
        raise RuntimeError("Fase 1 no completada. Ejecutar primero desde fase 1.")

    def _run():
        return synthesize(analysis)

    return checkpoint_or_run(checkpoint_path, _run)
