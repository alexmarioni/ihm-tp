# IHM-TP1 — Generador de Video desde PDF para TDAH

Pipeline de inteligencia artificial que convierte cualquier PDF conceptual en un video corto (8-15 segundos) optimizado para usuarios con TDAH, aplicando principios de psicología cognitiva e Interfaz Hombre-Máquina.

**Stack 100% gratuito** — no requiere tarjeta de crédito.

---

## ¿Qué hace?

Dado un PDF de entrada, el pipeline ejecuta 8 fases automáticamente:

| Fase | Descripción | Tecnología |
|------|-------------|------------|
| 1 | Extrae tema central, idea core, keywords y tono del PDF | Groq (llama-3.3-70b) |
| 2 | Genera 3 hooks de apertura y selecciona el mejor para TDAH | Groq |
| 3 | Crea tabla de traducción psicológica (IHM → elementos visuales) | Groq |
| 4 | Diseña storyboard de 3 escenas con parámetros de movimiento | Groq |
| 5 | Genera imágenes para cada escena | Pollinations.ai (FLUX) |
| 6 | Compone video vertical 1080x1920 con efecto Ken Burns | FFmpeg + Pillow |
| 7 | Genera narración en español y la mezcla con el video | edge-tts |
| 8 | Evalúa el resultado contra criterios de diseño TDAH | Groq |

Salida: `output/video_final.mp4` — video vertical 9:16, listo para móvil.

---

## Requisitos previos

- Python 3.11+
- FFmpeg instalado en el sistema

### Instalar FFmpeg (Windows)

```bash
winget install ffmpeg
```

Verificar que funcione:
```bash
ffmpeg -version
```

---

## Instalación

```bash
git clone https://github.com/alexmarioni/ihm-tp.git
cd ihm-tp
pip install -r requirements.txt
```

---

## Configuración

### 1. Obtener API key de Groq (gratis)

1. Entrá a [console.groq.com](https://console.groq.com)
2. Creá una cuenta gratuita (no requiere tarjeta)
3. En el menú lateral: **API Keys → Create API Key**
4. Copiá la key (empieza con `gsk_...`)

El plan gratuito incluye 500.000 tokens por día — más que suficiente para este pipeline.

### 2. Crear archivo `.env`

Copiá el archivo de ejemplo:
```bash
cp .env.example .env
```

Abrí `.env` y pegá tu API key:
```
GROQ_API_KEY=gsk_TU_CLAVE_AQUI
```

El resto de los valores ya tienen defaults razonables.

---

## Uso

### Preparar el PDF de entrada

Copiá tu PDF a la carpeta `input/`:
```bash
cp mi_documento.pdf input/documento.pdf
```

O especificá la ruta directamente al correr el pipeline.

### Correr el pipeline completo

```bash
python main.py
```

### Opciones

```bash
# Especificar un PDF diferente
python main.py --pdf ruta/a/mi_documento.pdf

# Retomar desde una fase específica (usa los checkpoints guardados)
python main.py --from 5

# Ver todas las opciones
python main.py --help
```

### Ejemplo de salida en consola

```
==================================================
IHM-TP1 — Generador de Video desde PDF
PDF: input/documento.pdf
Iniciando desde fase: 1
==================================================

[Fase 1] PDF Analysis
----------------------------------------
  Extrayendo texto del PDF...
  Texto extraído: 3420 palabras → enviando a Groq...

[Fase 2] Hook Synthesis
----------------------------------------
  Generando 3 hooks candidatos...
  Seleccionando el mejor hook para TDAH...

...

==================================================
Pipeline completado.
Video final: output/video_final.mp4 (4.2 MB)

QA: APROBADO — Puntaje: 87/100
  [OK] idea_unica: 90/100
  [OK] ortografia: 100/100
  [OK] captacion_atencion: 85/100
  ...
==================================================
```

---

## Sistema de checkpoints

Cada fase guarda su resultado en `output/` como JSON. Si el pipeline se interrumpe o querés ajustar algo, podés retomar desde cualquier fase sin re-ejecutar las anteriores (y sin gastar tokens de API).

```
output/
├── phase1_analysis.json      # análisis del PDF
├── phase2_hook.json          # hooks generados y seleccionado
├── phase3_psychology.json    # tabla psicológica IHM
├── phase4_storyboard.json    # storyboard completo
├── phase5_images/            # imágenes generadas por escena
├── phase6_segments/          # clips de video por escena
├── phase7_audio/             # narración MP3
├── phase8_qa.json            # reporte de calidad
└── video_final.mp4           # resultado final
```

Para regenerar solo las imágenes y el video (manteniendo el análisis y storyboard):
```bash
python main.py --from 5
```

---

## Estructura del proyecto

```
ihm-tp/
├── main.py                   # orquestador principal
├── phases/
│   ├── phase1_extraction.py  # PDF → análisis JSON
│   ├── phase2_synthesis.py   # generación y selección de hooks
│   ├── phase3_psychology.py  # tabla IHM → psicología
│   ├── phase4_storyboard.py  # diseño del storyboard
│   ├── phase5_images.py      # generación de imágenes (Pollinations.ai)
│   ├── phase6_video.py       # Ken Burns + text overlay (FFmpeg)
│   ├── phase7_audio.py       # TTS narración (edge-tts)
│   └── phase8_qa.py          # evaluación de calidad (Groq)
└── utils/
    ├── checkpoint.py         # sistema de checkpoints
    ├── groq_client.py        # cliente Groq con parsing JSON robusto
    └── text_overlay.py       # renderizado de texto con Pillow
```

---

## Variables de configuración (`.env`)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | **Requerida.** Tu API key de Groq |
| `INPUT_PDF` | `input/documento.pdf` | Ruta al PDF de entrada |
| `TARGET_DURATION` | `12` | Duración del video en segundos (8-15) |
| `VIDEO_WIDTH` | `1080` | Ancho del video en px |
| `VIDEO_HEIGHT` | `1920` | Alto del video en px |
| `VIDEO_FPS` | `24` | Frames por segundo |
| `TTS_VOICE` | `es-ES-AlvaroNeural` | Voz para la narración |
| `TTS_RATE` | `-10%` | Velocidad de la narración (negativo = más lento) |
| `IMAGE_SEED` | `42` | Semilla para reproducibilidad de imágenes |

### Voces disponibles (edge-tts)

| Voz | Acento | Género |
|-----|--------|--------|
| `es-ES-AlvaroNeural` | España | Masculino |
| `es-ES-ElviraNeural` | España | Femenino |
| `es-AR-TomasNeural` | Argentina | Masculino |
| `es-AR-ElenaNeural` | Argentina | Femenino |

---

## Contexto académico

Trabajo Práctico 1 — Interfaz Hombre-Máquina  
Tema: diseño de un MVP para generar videos breves desde PDFs conceptuales, con foco en usuarios con TDAH.

El pipeline aplica los siguientes principios cognitivos:
- Atención selectiva y saliencia visual
- Efecto de novedad y contraste
- Minimización de carga cognitiva
- Recompensa inmediata y anclaje emocional
