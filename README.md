# 🚀 MagicFile: Advanced GIF to SVG Converter & Image Utilities

MagicFile is a modern, high-performance web tool built with **Python (Flask)** and **Tailwind CSS**. It specializes in transforming animated GIFs into lightweight, background-free animated SVGs, alongside professional-grade image conversion and inpainting tools.

---

## ✨ Key Features

### 🎬 GIF to Animated SVG
- **Smart Conversion**: Transform any `.gif` into an `.svg`.
- **Background Removal**: Intelligent detection and removal of solid backgrounds (ideal for white/light backgrounds).
- **SMIL Animation**: Generates a single SVG file with optimized SMIL animations for web compatibility.

### 🖌️ Pro Inpainting & Watermark Removal
- **Interactive Canvas**: Drag and select areas to "magic erase" elements.
- **Context-Aware Fill**: Uses OpenCV (INPAINT_TELEA) to reconstruct pixels under the selection.
- **Transparency Preservation**: Cleans watermarks while keeping the alpha channel intact.

### 🔄 Multi-Format Converter
- **SVG to Raster**: Convert SVG icons or graphics to **PNG**, **JPG**, **WEBP**, or even **Transparent GIF**.
- **Batch Processing**: Quick conversion with custom tolerance for background removal.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ / Flask
- **Image Processing**:
  - `Pillow` (PIL) for raster manipulation.
  - `CairoSVG` for vector-to-raster conversion.
  - `OpenCV` (cv2) for inpainting logic.
  - `ImageIO` for GIF frame extraction.
- **Frontend**: Tailwind CSS + Vanilla JS (Interactive UI).
- **Deployment**: Configured for **Vercel** (`vercel.json` included).

---

## 🚀 Getting Started

### Prerequisites
Ensure you have **Python 3.10+** installed.

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd file-converter
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally

```bash
python app.py
```
Visit `http://127.0.0.1:5000` to start converting!

---

## 📂 Project Structure

```text
├── api/            # Vercel serverless entry point
├── app/            # Main application logic & routes
├── static/         # Assets & Tailwind styles
├── templates/      # Jinja2 HTML templates
├── uploads/        # Temporary storage for processing
├── app.py          # Local development entry
├── vercel.json     # Deployment configuration
└── requirements.txt # Project dependencies
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

*Built with ❤️ by Kevingedev*
