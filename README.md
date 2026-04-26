# cli-web-flow

A command-line tool that automates image generation and Image-to-Image editing on Google Labs Flow. Manages authentication through injected cookies and provides a robust interface for terminal-based creation.

## Prerequisites

- **MS Edge** browser installed
- **Python 3.10+** installed
- **Git** installed
- **Playwright** (installed automatically with the tool)

## Installation

### Option 1: pipx (Recommended for global CLI tools)

```bash
git clone https://github.com/indfn/Flow-Web-CLI-Tool.git
cd cli-web-flow
pipx install .
playwright install msedge
```

### Option 2: uv (Fast alternative)

```bash
git clone https://github.com/indfn/Flow-Web-CLI-Tool.git
cd cli-web-flow
uv pip install .
playwright install msedge
```

### Option 3: Development Install (with venv)

```bash
git clone https://github.com/indfn/Flow-Web-CLI-Tool.git
cd cli-web-flow
python3 -m venv venv
source venv/bin/activate
pip install -e .
playwright install msedge
```

## Authentication Setup

1. Open MS Edge and log into [Google Labs Flow](https://labs.google/flow)
2. Export cookies:
   - Open DevTools (`F12`) → Application tab → Cookies → Copy as JSON
   - Or use a cookie export extension
3. Save the cookies to a file (e.g., `cookies.json`)
4. Configure the CLI:

```bash
cli-web-flow login
# Enter the path to your cookies.json when prompted
```

## Commands

### Authentication & Status

**Login** - Set the path to your `cookies.json`:
```bash
cli-web-flow login
```

**Status** - Check login session and active project:
```bash
cli-web-flow status
```

### Project Management

**Create Project** - Start a fresh project:
```bash
cli-web-flow create-project --name "My Scene"
```

**List Projects** - View all projects:
```bash
cli-web-flow list-projects
```

**Select Project** - Set the project for subsequent operations:
```bash
cli-web-flow select-project <project_uuid>
```

### Image Operations

**Generate Image** - Text-to-image generation:
```bash
cli-web-flow generate-image --prompt 'A futuristic neon city' --ratio '16:9' --model 'nanobanana 2' --count 1 --download-dest '~/Downloads/city.png'
```

**Edit Image** - Image-to-Image editing:
```bash
# Via local upload
cli-web-flow edit-image --image './photo.jpg' --prompt 'Add a sunset' --ratio '16:9' --model 'nanobanana 2' --count 1 --download-dest './result.png'

# Via project index
cli-web-flow edit-image --image 0 --prompt 'Make it 8-bit style' --ratio '1:1' --model 'imagen 4' --count 1
```

**List Images** - List images in the active project:
```bash
cli-web-flow list-images
```

**Download** - Explicitly download an existing image:
```bash
cli-web-flow download --image 0 --to-path './out.png'
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `--prompt` | Description of the desired result |
| `--ratio` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` |
| `--model` | Model: `nanobanana 2`, `nanobanana pro`, `imagen 4` |
| `--count` | Number of outputs per prompt (1-4) |
| `--download-dest` | Path to save results |

## License

MIT License
