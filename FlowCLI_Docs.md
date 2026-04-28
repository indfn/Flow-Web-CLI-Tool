# Flow CLI User Guide

`cli-web-flow` is a command-line tool that automates image generation and Image-to-Image editing on Google Labs Flow. It manages authentication through injected cookies and provides a robust interface for terminal-based AI creation.

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

**Generate Image** - Text-to-image generation (the end path for --download-dest can be the name of your downloaded picture):
```bash
cli-web-flow generate-image --prompt 'A futuristic neon city' --ratio '16:9' --model 'nanobanana 2' --count 1 --download-dest '/home/user/Downloads/picture_of_city'
```

**Edit Image** - Image-to-Image editing:
```bash
# Via local upload
cli-web-flow edit-image --image '/path/to/image' --prompt 'Add a sunset' --ratio '16:9' --model 'nanobanana 2' --count 1 --download-dest '/home/user/Downloads/sunset'

# Via project index (only edits the latest picture in the project)
cli-web-flow edit-image --image 0 --prompt 'Make it 8-bit style' --ratio '1:1' --model 'imagen 4' --count 1 --download-dest '/path/to/download/name'
```

Note: edit-image with attatching images via image index (--image x) currently only supports attatching the latest image in the project (--image 0) so any other number will be defaulted to 0.

**List Images** - List images in the active project (returns all image ids in the project, but will also say "No prompt detected" since the website dosen't render the description of an image unless hovered upon):
```bash
cli-web-flow list-images
```

**Download** - Explicitly download an existing image (supports all images in the project, with latest being index 0):
```bash
cli-web-flow download --image 0 --to-path '/path/to/download/name'
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `--prompt` | Description of the desired result |
| `--ratio` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` |
| `--model` | Model: `nanobanana 2`, `nanobanana pro`, `imagen 4` |
| `--count` | Number of outputs per prompt (1-4) |
| `--download-dest` | Path to save results |
