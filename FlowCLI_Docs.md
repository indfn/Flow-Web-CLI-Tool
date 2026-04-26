# Flow CLI User Guide

`cli-web-flow` is a command-line tool that automates image generation and Image-to-Image editing on Google Labs Flow. It manages authentication through injected cookies and provides a robust interface for terminal-based AI creation.

## Installation & Setup

1. **Prerequisites**: Ensure you have MS Edge installed.
2. **Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   playwright install msedge
   ```
3. **Authentication**: Export your cookies from a logged-in Google Labs Flow session into a `cookies.json` file.

## Commands

### Authentication & Status
- **login**: Set the path to your `cookies.json`.
  ```bash
  cli-web-flow login
  ```
- **status**: Check login session and active project.
  ```bash
  cli-web-flow status
  ```

### Project Management
- **create-project**: Start a fresh project.
  ```bash
  cli-web-flow create-project --name "My Scene"
  ```
- **list-projects**: View all projects.
  ```bash
  cli-web-flow list-projects
  ```
- **select-project**: Set the project for subsequent operations.
  ```bash
  cli-web-flow select-project <project_uuid>
  ```

### Image Operations
- **generate-image**: Create from text.
  ```bash
  cli-web-flow generate-image --prompt "A futuristic neon city" --ratio 16:9 --model "nanobanana 2" --count 1 --download-dest "~/Downloads/city.png"
  ```
- **edit-image**: Image-to-Image using an upload or project index.
  ```bash
  # Via local upload
  cli-web-flow edit-image --image "./photo.jpg" --prompt "Add a sunset" --count 1 --download-dest "./result.png"

  # Via project index
  cli-web-flow edit-image --image 0 --prompt "Make it 8-bit style" --count 1
  ```
- **list-images**: List images in the active project.
  ```bash
  cli-web-flow list-images
  ```
- **download**: Explicitly download an existing image.
  ```bash
  cli-web-flow download --image 0 --to-path "./out.png" --upscale 2x
  ```

## Parameters
- `--prompt`: Description of the desired result.
- `--ratio`: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`.
- `--model`: `nanobanana 2`, `nanobanana pro`, `imagen 4`.
- `--count`: `1` to `4` (outputs per prompt).
- `--download-dest`: Path to save results (supports directory or file template).
