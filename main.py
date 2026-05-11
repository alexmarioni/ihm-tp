"""
IHM-TP1: Generador de video desde PDF para usuarios con TDAH
Pipeline de 8 fases — stack gratuito (Groq + Pollinations.ai + edge-tts)

Uso:
  python main.py                        # pipeline completo desde fase 1
  python main.py --from 5               # retomar desde fase 5 (usa checkpoints anteriores)
  python main.py --pdf otra_entrada.pdf # especificar PDF diferente
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from phases import (
    phase1_extraction,
    phase2_synthesis,
    phase3_psychology,
    phase4_storyboard,
    phase5_images,
    phase6_video,
    phase7_audio,
    phase8_qa,
)
from utils.checkpoint import load_checkpoint

OUTPUT_DIR = "output"

PHASES = [
    (1, "PDF Analysis",        phase1_extraction),
    (2, "Hook Synthesis",      phase2_synthesis),
    (3, "Psychology Table",    phase3_psychology),
    (4, "Storyboard Design",   phase4_storyboard),
    (5, "Image Generation",    phase5_images),
    (6, "Video Composition",   phase6_video),
    (7, "Voice & Audio",       phase7_audio),
    (8, "QA Evaluation",       phase8_qa),
]


def print_qa_summary(output_dir: str) -> None:
    qa = load_checkpoint(os.path.join(output_dir, "phase8_qa.json"))
    if not qa:
        return

    status = "APROBADO" if qa.get("aprobado") else "NO APROBADO"
    score = qa.get("puntaje_total", 0)
    print(f"\n{'='*50}")
    print(f"QA: {status} — Puntaje: {score}/100")

    criterios = qa.get("criterios", {})
    for nombre, datos in criterios.items():
        p = datos.get("puntaje", 0)
        obs = datos.get("observacion", "")
        flag = "OK" if p >= 75 else "BAJO"
        print(f"  [{flag}] {nombre}: {p}/100 — {obs}")

    recomendaciones = qa.get("recomendaciones", [])
    if recomendaciones:
        print("\nRecomendaciones:")
        for r in recomendaciones:
            print(f"  • {r}")

    fase_retry = qa.get("fase_a_reintentar")
    if fase_retry:
        print(f"\nSugerencia: reintentar desde fase {fase_retry}")
        print(f"  python main.py --from {fase_retry}")

    print(f"{'='*50}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de video desde PDF (IHM-TP1)")
    parser.add_argument("--from", dest="start_phase", type=int, default=1,
                        help="Fase desde la que iniciar (1-8, default: 1)")
    parser.add_argument("--pdf", dest="pdf_path",
                        default=os.getenv("INPUT_PDF", "input/documento.pdf"),
                        help="Ruta al PDF de entrada")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF no encontrado: {args.pdf_path}")
        print("Coloca el PDF en input/documento.pdf o usa --pdf <ruta>")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"IHM-TP1 — Generador de Video desde PDF")
    print(f"PDF: {args.pdf_path}")
    print(f"Iniciando desde fase: {args.start_phase}")
    print(f"{'='*50}\n")

    for num, name, module in PHASES:
        if num < args.start_phase:
            print(f"[Fase {num}] {name} — omitida")
            continue

        print(f"\n[Fase {num}] {name}")
        print(f"{'-'*40}")
        try:
            module.run(pdf_path=args.pdf_path, output_dir=OUTPUT_DIR)
        except Exception as e:
            print(f"\nError en Fase {num}: {e}")
            print(f"Para reintentar: python main.py --from {num} --pdf {args.pdf_path}")
            sys.exit(1)

    final_video = os.path.join(OUTPUT_DIR, "video_final.mp4")
    print(f"\n{'='*50}")
    print(f"Pipeline completado.")
    if os.path.exists(final_video):
        size_mb = os.path.getsize(final_video) / (1024 * 1024)
        print(f"Video final: {final_video} ({size_mb:.1f} MB)")
    print_qa_summary(OUTPUT_DIR)


if __name__ == "__main__":
    main()
