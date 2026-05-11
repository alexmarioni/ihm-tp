"""
Fase 8: Evaluación QA del pipeline — Groq evalúa el storyboard y outputs textualmente.
Salida: output/phase8_qa.json
"""

import json
import os

from utils.checkpoint import checkpoint_or_run, load_checkpoint
from utils.groq_client import call_llm_json

SYSTEM = (
    "Eres un evaluador experto en IHM y diseño de medios para usuarios con TDAH. "
    "Responde ÚNICAMENTE con JSON válido."
)

PROMPT_TEMPLATE = """Evalúa el siguiente video generado por un pipeline de IA a partir de un PDF.

RESUMEN DEL PDF ORIGINAL:
{analysis}

STORYBOARD GENERADO:
{storyboard}

NARRACIÓN POR ESCENA:
{narracion}

TEXTOS EN PANTALLA:
{textos_pantalla}

DURACIÓN TOTAL: {duracion_total} segundos

Evalúa con puntaje 0-100 cada criterio. Sé crítico pero justo.

CRITERIOS:
1. idea_unica: ¿comunica UNA sola idea central? (TDAH requiere sin fragmentación)
2. ortografia: ¿hay errores ortográficos en textos de pantalla y narración?
3. captacion_atencion: ¿el hook captura atención en menos de 3 segundos?
4. carga_cognitiva: ¿el texto en pantalla es mínimo (≤5 palabras por escena)?
5. duracion_correcta: ¿la duración está entre 8 y 15 segundos? (binario: 100 o 0)
6. texto_minimal: ¿los textos son concisos y no sobrecargan visualmente?
7. narracion_complementa: ¿la narración complementa sin repetir exactamente el texto visual?
8. pertinencia_pdf: ¿el contenido del video se deriva del PDF y no de temas inventados?

UMBRALES: mínimo 75 en cada criterio, promedio global ≥ 80 para aprobar.

Responde con este JSON:
{{
  "aprobado": true/false,
  "puntaje_total": <promedio 0-100>,
  "criterios": {{
    "idea_unica": {{"puntaje": 0-100, "observacion": "..."}},
    "ortografia": {{"puntaje": 0-100, "observacion": "..."}},
    "captacion_atencion": {{"puntaje": 0-100, "observacion": "..."}},
    "carga_cognitiva": {{"puntaje": 0-100, "observacion": "..."}},
    "duracion_correcta": {{"puntaje": 0-100, "observacion": "..."}},
    "texto_minimal": {{"puntaje": 0-100, "observacion": "..."}},
    "narracion_complementa": {{"puntaje": 0-100, "observacion": "..."}},
    "pertinencia_pdf": {{"puntaje": 0-100, "observacion": "..."}}
  }},
  "recomendaciones": ["..."],
  "fase_a_reintentar": null
}}

Si no aprueba, "fase_a_reintentar" debe indicar el número de fase (2-4) donde reintentar."""


def evaluate(analysis: dict, storyboard: dict) -> dict:
    narracion = "\n".join(
        f"Escena {e['orden']}: \"{e.get('texto_narracion', '')}\""
        for e in storyboard["escenas"]
    )
    textos_pantalla = "\n".join(
        f"Escena {e['orden']}: \"{e.get('texto_pantalla') or 'sin texto'}\""
        for e in storyboard["escenas"]
    )

    prompt = PROMPT_TEMPLATE.format(
        analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
        storyboard=json.dumps(storyboard, ensure_ascii=False, indent=2),
        narracion=narracion,
        textos_pantalla=textos_pantalla,
        duracion_total=storyboard.get("duracion_total", 12),
    )
    return call_llm_json(prompt, system=SYSTEM)


def run(pdf_path: str, output_dir: str) -> dict:
    analysis = load_checkpoint(os.path.join(output_dir, "phase1_analysis.json"))
    storyboard = load_checkpoint(os.path.join(output_dir, "phase4_storyboard.json"))

    if not all([analysis, storyboard]):
        raise RuntimeError("Fases 1 y 4 deben completarse primero.")

    checkpoint_path = os.path.join(output_dir, "phase8_qa.json")

    def _run():
        print("  Evaluando pipeline con Groq...")
        return evaluate(analysis, storyboard)

    return checkpoint_or_run(checkpoint_path, _run)
