# src/cli_web_flow/cli.py
import click
import sys
import os
from cli_web_flow.auth import save_cookie_path, get_cookie_path, save_project_id, get_project_id
from cli_web_flow.automation import (
    generate_image_automation, 
    AutomationError,
    list_projects_automation,
    create_project_automation,
    list_images_automation,
    edit_image_automation,
    download_image_automation
)

@click.group()
def cli():
    pass

@cli.command()
@click.option("--name", help="Optional project name")
def create_project(name):
    cookie_path = get_cookie_path()
    if not cookie_path:
        click.echo("Error: Not logged in.", err=True)
        sys.exit(1)
    try:
        project_id = create_project_automation(cookie_path, name)
        save_project_id(project_id)
        click.echo(f"Created and selected new project: {project_id}")
    except AutomationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def login():
    cookie_path = click.prompt("paste the path to your cookies.json")
    save_cookie_path(cookie_path)
    click.echo("Logged in")

@cli.command()
def status():
    path = get_cookie_path()
    project_id = get_project_id()
    if path:
        click.echo(f"Cookie Path: {path}")
        click.echo("Verifying login status...")
        from cli_web_flow.automation import verify_auth_automation
        if verify_auth_automation(path):
            click.echo("Status: Logged in (Active Session)")
        else:
            click.echo("Status: Session Expired or Invalid Cookies", err=True)
            
        if project_id:
            click.echo(f"Active Project: {project_id}")
        else:
            click.echo("No project selected")
    else:
        click.echo("Not logged in")

@cli.command()
def list_projects():
    cookie_path = get_cookie_path()
    if not cookie_path:
        click.echo("Error: Not logged in.", err=True)
        sys.exit(1)
    try:
        projects = list_projects_automation(cookie_path)
        for p in projects:
            click.echo(f"{p['id']}: {p['name']}")
    except AutomationError as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument("project_id")
def select_project(project_id):
    save_project_id(project_id)
    click.echo(f"Selected project: {project_id}")

@cli.command()
def list_images():
    cookie_path = get_cookie_path()
    project_id = get_project_id()
    if not cookie_path or not project_id:
        click.echo("Error: Not logged in or no project selected.", err=True)
        sys.exit(1)
    try:
        images = list_images_automation(cookie_path, project_id)
        if not images:
            click.echo("No images found in this project.")
            return
        for img in images:
            click.echo(f"[{img['index']}] \"{img.get('prompt', 'Unknown')}\" (Ref: {img['ref']})")
    except AutomationError as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option("--prompt", required=True, help="Text prompt for image generation")
@click.option("--ratio", required=True, type=click.Choice(["1:1", "16:9", "9:16", "4:3", "3:4"]), help="Aspect ratio")
@click.option("--model", required=True, type=click.Choice(["nanobanana 2", "nanobanana pro", "imagen 4"]), help="Model to use")
@click.option("--count", default=1, type=click.IntRange(1, 4), help="Number of images to generate (1-4)")
@click.option("--download-dest", help="Optional path to download the result")
def generate_image(prompt, ratio, model, count, download_dest):
    cookie_path = get_cookie_path()
    project_id = get_project_id()
    if not cookie_path or not project_id:
        click.echo("Error: Not logged in or no project selected.", err=True)
        sys.exit(1)

    click.echo(f"Generating {count} image(s) in project {project_id}...")
    try:
        generate_image_automation(
            cookie_path=cookie_path,
            prompt=prompt,
            ratio=ratio,
            model=model,
            count=count,
            download_dest=download_dest,
            project_id=project_id
        )
        click.echo("Generation triggered successfully.")
        
        if not download_dest:
            if click.confirm("Would you like to download the generated images?"):
                dest = click.prompt("Please paste the path to download into")
                
                # Handle directory paths by appending a default filename
if os.path.isdir(dest) or dest.endswith('/') or dest.endswith('\\'):
                os.makedirs(dest, exist_ok=True)
                dest = os.path.join(dest, "generated_image.png")

            click.echo(f"Downloading {count} image(s)...")
for i in range(count):
                current_dest = dest
                if count > 1:
                    base, ext = os.path.splitext(dest)
                    current_dest = f"{base}_{i}{ext}"

                download_image_automation(cookie_path, project_id, str(i), current_dest)
                click.echo(f"Downloaded image {i} to {current_dest}")
                
    except AutomationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option("--image", required=True, help="Local path or Project Image Index")
@click.option("--prompt", required=True, help="Text prompt")
@click.option("--ratio", required=True, type=click.Choice(["1:1", "16:9", "9:16", "4:3", "3:4"]), help="Aspect ratio")
@click.option("--model", required=True, type=click.Choice(["nanobanana 2", "nanobanana pro", "imagen 4"]), help="Model to use")
@click.option("--count", default=1, type=click.IntRange(1, 4), help="Number of images to generate (1-4)")
@click.option("--download-dest", help="Optional path to download the result")
def edit_image(image, prompt, ratio, model, count, download_dest):
    cookie_path = get_cookie_path()
    project_id = get_project_id()
    if not cookie_path or not project_id:
        click.echo("Error: Not logged in or no project selected.", err=True)
        sys.exit(1)
    try:
        edit_image_automation(
            cookie_path=cookie_path, 
            project_id=project_id, 
            image_ref=image, 
            prompt=prompt, 
            ratio=ratio, 
            model=model,
            count=count,
            download_dest=download_dest
        )
        click.echo("Edit triggered successfully.")
        
if not download_dest:
        if click.confirm("Would you like to download the generated image?"):
            dest = click.prompt("Please paste the path to download into")
            if os.path.isdir(dest) or dest.endswith('/') or dest.endswith('\\'):
                os.makedirs(dest, exist_ok=True)
                dest = os.path.join(dest, "edited_image.png")

            click.echo(f"Downloading {count} image(s)...")

            # Loop through all generated images
            for i in range(count):
                current_dest = dest
                if count > 1:
                    base, ext = os.path.splitext(dest)
                    current_dest = f"{base}_{i}{ext}"

                # We use index 0 because the newest ones are usually at the top
                # or they shifted. For simplicity we'll try to download the first 'count' images.
                download_image_automation(cookie_path, project_id, str(i), current_dest)
                click.echo(f"Downloaded image {i} to {current_dest}")
    except AutomationError as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option("--image", required=True, help="Project Image Index")
@click.option("--to-path", required=True, help="Download destination")
def download(image, to_path):
    cookie_path = get_cookie_path()
    project_id = get_project_id()
    if not cookie_path or not project_id:
        click.echo("Error: Not logged in or no project selected.", err=True)
        sys.exit(1)
    try:
        download_image_automation(cookie_path, project_id, image, to_path)
        click.echo(f"Downloaded to {to_path}")
    except AutomationError as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    cli()
