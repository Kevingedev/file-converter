# Conversor GIF → SVG animado (Python + Tailwind)

Aplicación web sencilla construida con **Python (Flask)** que permite:

- Subir un archivo **GIF animado**
- Eliminar un fondo claro/blanco
- Generar un archivo **SVG animado** que mantiene la animación (los frames se incrustan como imágenes PNG en el SVG y se animan por opacidad)

> Nota: el resultado es un archivo `.svg` que contiene imágenes raster (PNG) animadas, no un vectorizado perfecto. Sin embargo, cumple con el flujo web de usar un formato SVG animado y fondo transparente.

## Requisitos

- Python 3.10+ (recomendado)

## Instalación

```bash
cd "/home/penascalf5/Escritorio/CURSO FULLSTACK/file-converter"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
source .venv/bin/activate
python app.py
```

Luego abre en tu navegador:

- http://127.0.0.1:5000

## Uso

1. En la página principal, arrastra un archivo **.gif** animado o haz clic para seleccionarlo.
2. Pulsa **“Convertir a SVG sin fondo”**.
3. Se descargará un archivo `animacion_sin_fondo.svg`.

Para mejores resultados:

- Usa GIFs con **fondo claro/blanco** y el sujeto bien contrastado.
- Evita fondos muy texturizados o de muchos colores.


