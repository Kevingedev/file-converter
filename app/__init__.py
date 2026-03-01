from __future__ import annotations

from pathlib import Path
import io
import os
import base64

from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from PIL import Image
import imageio.v2 as imageio
import cairosvg

# En Vercel sólo se puede escribir en /tmp, así que usamos esa ruta para subidas temporales
BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = Path(os.environ.get("TMPDIR", "/tmp"))
UPLOAD_DIR = TMP_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def detect_background_color(frame: Image.Image) -> tuple[int, int, int]:
    """
    Intenta detectar el color de fondo tomando una muestra
    de los bordes del primer frame (promedio de píxeles).
    Esto permite eliminar fondos que no sean exactamente blancos.
    """
    frame = frame.convert("RGBA")
    width, height = frame.size
    pixels = frame.load()

    samples: list[tuple[int, int, int, int]] = []

    # Muestra: filas superior e inferior
    for x in range(width):
        samples.append(pixels[x, 0])
        samples.append(pixels[x, height - 1])

    # Muestra: columnas izquierda y derecha
    for y in range(height):
        samples.append(pixels[0, y])
        samples.append(pixels[width - 1, y])

    # Calcula el promedio sólo de los canales RGB
    if not samples:
        return (255, 255, 255)

    r_sum = g_sum = b_sum = 0
    count = 0
    for r, g, b, a in samples:
        r_sum += r
        g_sum += g
        b_sum += b
        count += 1

    return (r_sum // count, g_sum // count, b_sum // count)


def remove_background(
    frame: Image.Image,
    bg_color: tuple[int, int, int],
    tolerance: int = 35,
) -> Image.Image:
    """
    Quita el fondo que es similar al color de fondo detectado.
    `tolerance` controla cuánta diferencia se permite (cuanto mayor, más agresivo).
    """
    frame = frame.convert("RGBA")
    datas = frame.getdata()

    br, bg, bb = bg_color

    new_data = []
    for r, g, b, a in datas:
        # Distancia "Manhattan" al color de fondo
        dist = abs(r - br) + abs(g - bg) + abs(b - bb)
        if dist <= tolerance:
            new_data.append((r, g, b, 0))  # transparente
        else:
            new_data.append((r, g, b, a))
    frame.putdata(new_data)
    return frame


def gif_to_animated_svg(gif_path: Path) -> bytes:
    """
    Convierte un GIF animado en un SVG animado.
    Para mantener la animación de forma razonable y simple, incrustamos
    cada frame como imagen raster dentro del SVG y animamos su opacidad.
    Técnicamente no es vector puro, pero el archivo final es un .svg animado
    con el fondo eliminado.
    """
    reader = imageio.get_reader(gif_path)
    frames: list[Image.Image] = []
    durations: list[float] = []

    # Leemos el primer frame para detectar color de fondo
    try:
        first_frame_array = reader.get_data(0)
    except IndexError:
        raise ValueError("El GIF no contiene frames.")

    first_frame_img = Image.fromarray(first_frame_array)
    bg_color = detect_background_color(first_frame_img)

    meta = reader.get_meta_data()
    base_duration = meta.get("duration", 100) / 1000.0  # a segundos

    # Volvemos a iterar sobre todos los frames
    for frame_array in reader:
        img = Image.fromarray(frame_array)
        img = remove_background(img, bg_color=bg_color)
        frames.append(img)
        durations.append(base_duration)

    if not frames:
        raise ValueError("No se pudieron leer frames del GIF.")

    width, height = frames[0].size

    # Convertimos todos los frames a PNG en memoria y los codificamos en base64
    import base64

    png_data_list: list[str] = []
    for img in frames:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        png_data_list.append(png_b64)

    total_frames = len(png_data_list)

    # Generamos SVG con animación por opacidad usando SMIL.
    # En cada instante sólo un frame tiene opacidad 1, el resto 0,
    # para que la animación sea fluida (sin parpadeos de múltiples imágenes).
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet">',
        "<style>",
        "svg { background: transparent; }",
        "</style>",
    ]

    frame_duration = durations[0] if durations else 0.1
    total_duration = frame_duration * total_frames

    # keyTimes comunes para todos los frames (de 0 a 1, dividido en N segmentos)
    key_times_values = []
    for i in range(total_frames + 1):
        t = i / total_frames
        key_times_values.append(f"{t:.4f}".rstrip("0").rstrip("."))
    key_times_str = ";".join(key_times_values)

    for idx, png_b64 in enumerate(png_data_list):
        # Para este frame, sólo el segmento idx tendrá opacidad 1, el resto 0
        values_list = []
        for j in range(total_frames):
            values_list.append("1" if j == idx else "0")
        # valor final para cerrar el ciclo (0)
        values_list.append("0")
        values_str = ";".join(values_list)

        svg_parts.append(
            f'<image id="f{idx}" href="data:image/png;base64,{png_b64}" '
            f'width="{width}" height="{height}" opacity="0">'
            f'<animate attributeName="opacity" dur="{total_duration}s" '
            f'repeatCount="indefinite" keyTimes="{key_times_str}" '
            f'values="{values_str}" calcMode="discrete" />'
            f"</image>"
        )

    svg_parts.append("</svg>")
    svg_str = "".join(svg_parts)
    return svg_str.encode("utf-8")


def create_app() -> Flask:
    # Indicamos a Flask dónde están las carpetas de templates y estáticos
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

    @app.route("/")
    def index():
        # Home explicativa
        return render_template("index.html", current_view="home")

    @app.route("/gif", methods=["GET", "POST"])
    def gif_view():
        if request.method == "POST":
            file = request.files.get("file")
            if not file or file.filename == "":
                flash("Por favor, selecciona un archivo GIF.", "error")
                return redirect(url_for("gif_view"))

            if not file.filename.lower().endswith(".gif"):
                flash("Solo se permiten archivos GIF animados.", "error")
                return redirect(url_for("gif_view"))

            # Guardar temporalmente el GIF en /tmp (compatible con Vercel)
            temp_path = UPLOAD_DIR / file.filename
            file.save(temp_path)

            try:
                svg_bytes = gif_to_animated_svg(temp_path)
            except Exception as e:
                flash(f"Error al procesar el GIF: {e}", "error")
                return redirect(url_for("gif_view"))
            finally:
                # Limpiar el archivo subido
                if temp_path.exists():
                    temp_path.unlink()

            # Pasamos el SVG al template para poder previsualizarlo
            import base64

            svg_markup = svg_bytes.decode("utf-8", errors="ignore")
            svg_download_b64 = base64.b64encode(svg_bytes).decode("ascii")

            return render_template(
                "index.html",
                current_view="gif",
                svg_markup=svg_markup,
                svg_download_b64=svg_download_b64,
            )

        # Vista GIF sin resultado aún
        return render_template("index.html", current_view="gif")

    @app.route("/svg", methods=["GET", "POST"])
    def svg_view():
        if request.method == "POST":
            file = request.files.get("file")
            processing = request.form.get("processing", "none")
            action = request.form.get("action") or "convert_png"

            if not file or file.filename == "":
                flash("Por favor, selecciona un archivo SVG.", "error")
                return redirect(url_for("svg_view"))

            if not file.filename.lower().endswith(".svg"):
                flash("Solo se permiten archivos SVG.", "error")
                return redirect(url_for("svg_view"))

            svg_bytes = file.read()

            # Caso especial: quitar marcas de agua y devolver SVG
            if action == "watermark_remove_svg":
                try:
                    png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
                except Exception as e:
                    flash(f"Error al procesar el SVG: {e}", "error")
                    return redirect(url_for("svg_view"))

                img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                bg_color = detect_background_color(img)
                img = remove_background(img, bg_color=bg_color, tolerance=60)

                buf_png = io.BytesIO()
                img.save(buf_png, format="PNG")
                png_b64 = base64.b64encode(buf_png.getvalue()).decode("ascii")
                width, height = img.size

                svg_wrapped = (
                    f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                    f'<image href="data:image/png;base64,{png_b64}" '
                    f'width="{width}" height="{height}" /></svg>'
                )

                return send_file(
                    io.BytesIO(svg_wrapped.encode("utf-8")),
                    mimetype="image/svg+xml",
                    as_attachment=True,
                    download_name="svg_sin_marca.svg",
                )

            # Flujo normal: convertir a imagen raster en el formato elegido
            try:
                # Rasterizamos el SVG a PNG en memoria
                png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
            except Exception as e:
                flash(f"Error al procesar el SVG: {e}", "error")
                return redirect(url_for("svg_view"))

            # Abrimos la imagen rasterizada
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

            # Definimos configuración por defecto
            output_format = "PNG"
            mimetype = "image/png"
            download_name = "svg_convertido.png"

            # Acciones de limpieza según el tipo de procesamiento elegido
            if processing == "bg_remove":
                bg_color = detect_background_color(img)
                img = remove_background(img, bg_color=bg_color, tolerance=35)
            elif processing == "watermark_remove":
                # Versión más agresiva de quitar fondo para intentar reducir marcas de agua
                bg_color = detect_background_color(img)
                img = remove_background(img, bg_color=bg_color, tolerance=60)

            # Acciones de conversión según el formato de salida
            if action == "convert_jpg":
                output_format = "JPEG"
                mimetype = "image/jpeg"
                download_name = "svg_convertido.jpg"
            elif action == "convert_webp":
                output_format = "WEBP"
                mimetype = "image/webp"
                download_name = "svg_convertido.webp"
            elif action == "convert_gif":
                output_format = "GIF"
                mimetype = "image/gif"
                download_name = "svg_convertido.gif"
            else:  # convert_png u otros valores por defecto
                output_format = "PNG"
                mimetype = "image/png"
                download_name = "svg_convertido.png"

            buf = io.BytesIO()
            # Para JPEG no se admite transparencia, convertimos a RGB
            save_img = img
            if output_format == "JPEG":
                save_img = img.convert("RGB")
            save_img.save(buf, format=output_format)
            buf.seek(0)

            return send_file(
                buf,
                mimetype=mimetype,
                as_attachment=True,
                download_name=download_name,
            )

        # Vista SVG (formulario y opciones)
        return render_template("index.html", current_view="svg")

    @app.route("/png", methods=["GET"])
    def png_view():
        # Vista PNG (a futuro puedes conectar lógica real)
        return render_template("index.html", current_view="png")

    return app



