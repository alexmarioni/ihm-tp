"""
Fase 4: Diseño del storyboard completo (3 escenas) con parámetros para imagen, video y audio.
Salida: output/phase4_storyboard.json
"""

import json
import os

from utils.checkpoint import checkpoint_or_run, load_checkpoint
from utils.groq_client import call_llm_json

SYSTEM = (
    "Eres un director creativo especializado en videos cortos para redes sociales "
    "diseñados para usuarios con TDAH. Responde ÚNICAMENTE con JSON válido."
)

PROMPT_TEMPLATE = """ANÁLISIS DEL CONTENIDO:
{analysis}

HOOK SELECCIONADO: "{hook_texto}"

TABLA PSICOLÓGICA (úsala como restricciones de diseño):
{psychology}

Diseña un storyboard de 3 escenas para un video de {duracion_total} segundos (formato 1080x1920, vertical 9:16).

ESTRUCTURA OBLIGATORIA:
- Escena 1 "Hook" (orden 1): inicio_seg=0, fin_seg=3, duracion=3
- Escena 2 "Desarrollo" (orden 2): inicio_seg=3, fin_seg=9, duracion=6
- Escena 3 "Cierre" (orden 3): inicio_seg=9, fin_seg={duracion_total}, duracion={duracion_cierre}

RESTRICCIONES ESTRICTAS:
- descripcion_visual_pollinations: en INGLÉS, máximo 60 palabras, imagen vertical 9:16, fotorrealista o ilustrativa, incluye lighting + mood + composition; NO menciones texto ni palabras escritas en la imagen
- texto_pantalla: MÁXIMO 5 palabras por escena; puede ser null en escena 2
- texto_narracion: máximo 12 palabras por escena, voz en off en español, no compite con el texto en pantalla
- movimiento_ken_burns.tipo: uno de ["zoom_in", "zoom_out", "pan_left", "pan_right"]
- movimiento_ken_burns.zoom_inicio y zoom_fin: valores entre 1.0 y 1.25
- Todo el contenido debe derivarse 100% del PDF analizado

Responde con este JSON exacto:
{{
  "duracion_total": {duracion_total},
  "escenas": [
    {{
      "orden": 1,
      "nombre": "Hook",
      "inicio_seg": 0,
      "fin_seg": 3,
      "duracion": 3,
      "descripcion_visual_pollinations": "...",
      "texto_pantalla": "...",
      "texto_narracion": "...",
      "movimiento_ken_burns": {{
        "tipo": "zoom_in",
        "zoom_inicio": 1.0,
        "zoom_fin": 1.15
      }},
      "conceptos_psicologicos": ["atención selectiva", "saliencia visual"]
    }},
    {{
      "orden": 2,
      "nombre": "Desarrollo",
      "inicio_seg": 3,
      "fin_seg": 9,
      "duracion": 6,
      "descripcion_visual_pollinations": "...",
      "texto_pantalla": null,
      "texto_narracion": "...",
      "movimiento_ken_burns": {{
        "tipo": "zoom_out",
        "zoom_inicio": 1.1,
        "zoom_fin": 1.0
      }},
      "conceptos_psicologicos": ["carga cognitiva", "contraste"]
    }},
    {{
      "orden": 3,
      "nombre": "Cierre",
      "inicio_seg": 9,
      "fin_seg": {duracion_total},
      "duracion": {duracion_cierre},
      "descripcion_visual_pollinations": "...",
      "texto_pantalla": "...",
      "texto_narracion": "...",
      "movimiento_ken_burns": {{
        "tipo": "pan_right",
        "zoom_inicio": 1.05,
        "zoom_fin": 1.1
      }},
      "conceptos_psicologicos": ["recompensa", "emoción"]
    }}
  ]
}}"""


def build_storyboard(analysis: dict, hook: dict, psychology: dict, duracion_total: int = 12) -> dict:
    hook_texto = hook.get("seleccionado", {}).get("texto", "")
    duracion_cierre = duracion_total - 9

    prompt = PROMPT_TEMPLATE.format(
        analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
        hook_texto=hook_texto,
        psychology=json.dumps(psychology.get("tabla_traduccion", []), ensure_ascii=False, indent=2),
        duracion_total=duracion_total,
        duracion_cierre=duracion_cierre,
    )
    return call_llm_json(prompt, system=SYSTEM, max_tokens=6000)


def run(pdf_path: str, output_dir: str) -> dict:
    analysis = load_checkpoint(os.path.join(output_dir, "phase1_analysis.json"))
    hook = load_checkpoint(os.path.join(output_dir, "phase2_hook.json"))
    psychology = load_checkpoint(os.path.join(output_dir, "phase3_psychology.json"))

    if not all([analysis, hook, psychology]):
        raise RuntimeError("Fases 1, 2 y 3 deben completarse primero.")

    target_duration = int(os.getenv("TARGET_DURATION", "12"))
    checkpoint_path = os.path.join(output_dir, "phase4_storyboard.json")

    def _run():
        print("  Generando storyboard con Groq...")
        return build_storyboard(analysis, hook, psychology, duracion_total=target_duration)

    return checkpoint_or_run(checkpoint_path, _run)
