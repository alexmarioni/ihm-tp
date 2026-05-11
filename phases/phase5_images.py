"""
Fase 5: Genera imágenes para cada escena usando Pollinations.ai (gratis, sin API key).
Salida: output/phase5_images/scene{N}_img0.png
"""

import os
import time
from pathlib import Path
from urllib.parse import quote

import requests

from utils.checkpoint import load_checkpoint

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
BASE_SEED = int(os.getenv("IMAGE_SEED", "42"))


def build_prompt(descripcion: str) -> str:
    suffix = (
        "vertical composition 9:16 aspect ratio, "
        "high quality, cinematic, no text, no words, no letters"
    )
    return f"{descripcion}, {suffix}"


def download_image(prompt: str, output_path: str, seed: int, retries: int = 3) -> bool:
    encoded = quote(prompt)
    url = (
        f"{POLLINATIONS_URL.format(prompt=encoded)}"
        f"?width={VIDEO_WIDTH}&height={VIDEO_HEIGHT}&nologo=true&seed={seed}&model=flux"
    )

    for attempt in range(1, retries + 1):
        try:
            print(f"    Descargando imagen (seed={seed})...")
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200 and len(resp.content) > 1000:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return True
            print(f"    Intento {attempt} falló (status={resp.status_code}), reintentando...")
        except requests.RequestException as e:
            print(f"    Error de red intento {attempt}: {e}")
        time.sleep(5 * attempt)

    return False


def generate_images(storyboard: dict, images_dir: str) -> dict:
    results = {}

    for escena in storyboard["escenas"]:
        n = escena["orden"]
        descripcion = escena.get("descripcion_visual_pollinations", "")
        if not descripcion:
            print(f"  Escena {n}: sin descripción visual, saltando.")
            continue

        prompt = build_prompt(descripcion)
        output_path = os.path.join(images_dir, f"scene{n}_img0.png")

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"  Escena {n}: imagen ya existe, saltando.")
            results[f"scene{n}"] = output_path
            continue

        print(f"  Escena {n} ({escena['nombre']}): generando imagen...")
        seed = BASE_SEED + n * 17
        success = download_image(prompt, output_path, seed=seed)

        if success:
            print(f"  Escena {n}: imagen guardada → {output_path}")
            results[f"scene{n}"] = output_path
        else:
            raise RuntimeError(f"No se pudo generar la imagen para escena {n} después de 3 intentos.")

        # Pausa entre requests para no saturar el servicio
        time.sleep(3)

    return {"images": results, "images_dir": images_dir}


def run(pdf_path: str, output_dir: str) -> dict:
    storyboard = load_checkpoint(os.path.join(output_dir, "phase4_storyboard.json"))
    if storyboard is None:
        raise RuntimeError("Fase 4 debe completarse primero.")

    images_dir = os.path.join(output_dir, "phase5_images")
    os.makedirs(images_dir, exist_ok=True)

    # No usamos checkpoint_or_run porque cada imagen tiene su propio estado
    return generate_images(storyboard, images_dir)
