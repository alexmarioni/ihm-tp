"""
Fase 3: Tabla de traducción psicológica — elementos del video → conceptos IHM.
Salida: output/phase3_psychology.json
"""

import json
import os

from utils.checkpoint import checkpoint_or_run, load_checkpoint
from utils.groq_client import call_llm_json

SYSTEM = (
    "Eres un experto en Interfaz Hombre-Máquina (IHM) y psicología cognitiva aplicada "
    "al diseño de medios para TDAH. Responde ÚNICAMENTE con JSON válido."
)

PROMPT_TEMPLATE = """CONTEXTO DEL VIDEO:
- Tema: {tema_central}
- Idea central: {idea_central}
- Hook seleccionado: "{hook_texto}"
- Emoción dominante: {emocion_dominante}
- Tono: {tono}

Genera una tabla de traducción psicológica que mapee los elementos del video a conceptos cognitivos.
Cubre OBLIGATORIAMENTE los 7 conceptos siguientes (uno por item):
1. atención selectiva
2. saliencia visual
3. novedad / efecto de orientación
4. contraste (visual y cognitivo)
5. carga cognitiva (minimización)
6. recompensa e inmediatez
7. emoción como ancla atencional

Para cada concepto explica:
- elemento_video: qué recurso audiovisual del video lo implementa
- concepto_psicologico: nombre exacto del concepto
- mecanismo: cómo funciona cognitivamente (1 oración)
- implementacion_tecnica: cómo se hace concretamente (ej: "Ken Burns zoom-in 1.0→1.15")

Responde con JSON:
{{
  "tabla_traduccion": [
    {{
      "elemento_video": "...",
      "concepto_psicologico": "...",
      "mecanismo": "...",
      "implementacion_tecnica": "..."
    }}
  ]
}}"""


def build_table(analysis: dict, hook: dict) -> dict:
    hook_texto = hook.get("seleccionado", {}).get("texto", "")
    prompt = PROMPT_TEMPLATE.format(
        tema_central=analysis.get("tema_central", ""),
        idea_central=analysis.get("idea_central", ""),
        hook_texto=hook_texto,
        emocion_dominante=analysis.get("emocion_dominante", ""),
        tono=analysis.get("tono", ""),
    )
    return call_llm_json(prompt, system=SYSTEM)


def run(pdf_path: str, output_dir: str) -> dict:
    analysis = load_checkpoint(os.path.join(output_dir, "phase1_analysis.json"))
    hook = load_checkpoint(os.path.join(output_dir, "phase2_hook.json"))

    if analysis is None or hook is None:
        raise RuntimeError("Fases 1 y 2 deben completarse primero.")

    checkpoint_path = os.path.join(output_dir, "phase3_psychology.json")

    def _run():
        print("  Generando tabla psicológica IHM...")
        return build_table(analysis, hook)

    return checkpoint_or_run(checkpoint_path, _run)
