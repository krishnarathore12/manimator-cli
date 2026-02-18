<div align="center">

```
 ███╗   ███╗ █████╗ ███╗   ██╗██╗███╗   ███╗ █████╗ ████████╗ ██████╗ ██████╗
 ████╗ ████║██╔══██╗████╗  ██║██║████╗ ████║██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
 ██╔████╔██║███████║██╔██╗ ██║██║██╔████╔██║███████║   ██║   ██║   ██║██████╔╝
 ██║╚██╔╝██║██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══██║   ██║   ██║   ██║██╔══██╗
 ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║██║ ╚═╝ ██║██║  ██║   ██║   ╚██████╔╝██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
```

**Natural Language → Mathematical Animations**

Turn plain-English prompts into polished `.mp4` animations using LLMs and [Manim](https://www.manim.community/).

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

🌐 **[Landing Page](https://y-three-mu-63.vercel.app/)**

</div>

---

## ✨ Features

- 🎬 **One-shot generation** — describe an animation in plain English, get a rendered `.mp4`
- 💬 **Interactive chat mode** — iterate on your animation with follow-up changes
- 🔄 **Auto-correction** — automatically fixes broken Manim code with LLM-powered retries
- 🎨 **Quality presets** — `low`, `medium`, `high`, `ultra` render quality
- 🤖 **Multi-provider** — supports **OpenAI**, **Anthropic**, **Google Gemini**, and **Ollama** (local)
- 📁 **Unique filenames** — each video iteration gets an auto-generated versioned name

## 📦 Installation

### Prerequisites

Make sure you have these installed:

- **Python 3.9+**
- **[Manim Community](https://docs.manim.community/en/stable/installation.html)** — the rendering engine
- **ffmpeg** — for video encoding
- **LaTeX** (optional) — for math text rendering (`texlive-latex` or equivalent)

### Install from GitHub

```bash
pip install git+https://github.com/krishnarathore12/manimator-cli.git
```

### Install from source (for development)

```bash
git clone https://github.com/krishnarathore12/manimator-cli.git
cd manimator-cli
pip install -e .
```

## 🚀 Quick Start

### 1. Configure your LLM provider

```bash
# Set your provider (openai, anthropic, gemini, or ollama)
manimator config --provider gemini

# Set your API key
manimator config --key YOUR_API_KEY

# Verify configuration
manimator config --show
```

### 2. Create an animation

```bash
manimator create "a blue circle that morphs into a red square"
```

### 3. Interactive chat mode (recommended)

```bash
manimator chat
```

This launches an interactive session:

```
🎬 Describe your animation: a spinning blue circle
  ✓ Output: spinning_blue_circle_v1.mp4

✏  Enter follow-up changes: make it red and add a bouncing square
  ✓ Output: spinning_blue_circle_v2.mp4

✏  Enter follow-up changes: done

┌──────────────────────────────────┐
│  🎞  Generated Videos            │
│  1  spinning_blue_circle_v1.mp4  │
│  2  spinning_blue_circle_v2.mp4  │
└──────────────────────────────────┘
👋 Chat session ended.
```

## 📖 Commands

| Command                          | Description                                |
| -------------------------------- | ------------------------------------------ |
| `manimator create <description>` | One-shot: generate and render an animation |
| `manimator chat`                 | Interactive: describe, render, and iterate |
| `manimator config`               | View or update configuration               |
| `manimator list-models`          | List available LLM models                  |

### Common Options

```bash
# Set render quality
manimator create "..." --quality high

# Choose provider and model
manimator create "..." --provider anthropic --model claude-sonnet-4-5

# Auto-open video after render
manimator create "..." --preview

# Set output directory
manimator create "..." --output ./my-videos

# Show generated code
manimator create "..." --verbose
```

## Example Prompts

Try these with `manimator create` or `manimator chat`:

```bash
manimator create "a blue circle that morphs into a red square"

manimator create "visualize the Pythagorean theorem with animated squares on each side"

manimator create "show a sine wave being drawn in real-time with a moving dot"

manimator create "animate sorting an array of bars using bubble sort"

manimator create "draw a fractal tree that grows branch by branch"

manimator create "show how matrix multiplication works step by step with 2x2 matrices"

manimator create "a 3D rotating cube with colored faces"

manimator create "animate the derivative of x^2 showing the tangent line sliding along the curve"
```

## 🛠️ Development

```bash
# Clone and install in dev mode
git clone https://github.com/krishnarathore12/manimator-cli.git
cd manimator-cli
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
