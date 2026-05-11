"""
Fase 1: Extrae texto del PDF y genera un análisis estructurado con Groq.
Salida: output/phase1_analysis.json
"""

import os

import fitz  # PyMuPDF

from utils.checkpoint import checkpoint_or_run, save_checkpoint
from utils.groq_client import call_llm_json

CHECKPOINT = "output/phase1_analysis.json"

SYSTEM = (
    "Eres un analista de contenido experto en comunicación para personas con TDAH. "
    "Responde ÚNICAMENTE con JSON válido, sin markdown ni texto adicional."
)

PROMPT_TEMPLATE = """Se te proporciona el texto completo de un PDF conceptual académico.
Tu tarea es extraer la información estructural más relevante del documento.

TEXTO DEL PDF:
\"\"\"
{text}
\"\"\"

Responde ÚNICAMENTE con un objeto JSON válido con exactamente estas claves:
- tema_central: string (máximo 10 palabras, el tema principal)
- idea_central: string (una sola oración, máximo 20 palabras, la idea más importante)
- tres_ideas_importantes: array de exactamente 3 strings (cada uno máximo 15 palabras)
- palabras_clave: array de 5 a 7 strings (términos clave del documento)
- tono: uno de estos valores exactos: "urgente", "informativo", "inspirador", "critico", "reflexivo"
- audiencia: string (descripción de la audiencia objetivo, máximo 15 palabras)
- emocion_dominante: string (una emoción principal que debe provocar el video, máximo 3 palabras)

No incluyas texto fuera del JSON. No uses markdown. Solo JSON puro."""


def extract_pdf_text(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def analyze(pdf_path: str) -> dict:
    print("  Extrayendo texto del PDF...")
    text = extract_pdf_text(pdf_path)
    # Limitar a ~6000 palabras para no exceder contexto
    words = text.split()
    if len(words) > 6000:
        text = " ".join(words[:6000])
    print(f"  Texto extraído: {len(words)} palabras → enviando a Groq...")
    result = call_llm_json(PROMPT_TEMPLATE.format(text=text), system=SYSTEM)
    return result


def run(pdf_path: str, output_dir: str) -> dict:
    checkpoint_path = os.path.join(output_dir, "phase1_analysis.json")

    def _run():
        return analyze(pdf_path)

    return checkpoint_or_run(checkpoint_path, _run)
