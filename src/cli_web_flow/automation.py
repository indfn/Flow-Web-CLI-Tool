# src/cli_web_flow/automation.py
import json
import time
import os
import logging
from typing import Optional, List, Dict
from playwright.sync_api import sync_playwright, Page, BrowserContext

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://labs.google/fx/tools/flow"

class AutomationError(Exception):
    pass

def _load_cookies(context: BrowserContext, cookie_path: str) -> None:
    try:
        with open(cookie_path, 'r') as f:
            cookies = json.load(f)
        
        context.clear_cookies()
        processed_cookies = []
        for cookie in cookies:
            c = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain'),
                'path': cookie.get('path', '/'),
                'secure': cookie.get('secure', True),
                'httpOnly': cookie.get('httpOnly', False),
                'sameSite': cookie.get('sameSite', 'Lax') if cookie.get('sameSite') in ['Strict', 'Lax', 'None'] else 'Lax'
            }
            if not c['domain']:
                continue
            if ":" in c['domain']:
                c['domain'] = c['domain'].split(":")[0]
            
            processed_cookies.append(c)
        
        context.add_cookies(processed_cookies)
    except Exception as e:
        raise AutomationError(f"Failed to load cookies from {cookie_path}: {e}")

def generate_image_automation(
    cookie_path: Optional[str],
    prompt: str,
    ratio: str,
    model: str,
    download_dest: Optional[str] = None,
    project_id: Optional[str] = None,
    count: int = 1
) -> None:
    if not cookie_path:
        raise AutomationError("Cookie path not provided")
    if not project_id:
        raise AutomationError("Project ID not provided. Use 'select-project' first.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            _load_cookies(context, cookie_path)

            page = context.new_page()
            project_url = f"{BASE_URL}/project/{project_id}"
            page.goto(project_url, wait_until="networkidle")
            page.wait_for_timeout(5000)

            # --- Clear Overlays ---
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
            close_btns = page.locator('button:has-text("Got it"), button:has-text("Close"), button:has-text("close"), button:has-text("Next"), [aria-label*="Close"]').all()
            for btn in close_btns:
                try:
                    if btn.is_visible():
                        btn.click(timeout=2000)
                        page.wait_for_timeout(500)
                except: pass

            # --- Settings Adjustment ---
            settings_btn = page.locator('button:has-text("Nano Banana"), button:has-text("Imagen"), button:has-text("Genie")').first
            if settings_btn.count() > 0:
                settings_btn.click()
                page.wait_for_timeout(2000)

                # Set Model
                model_dropdown = page.locator('button:has-text("arrow_drop_down")').first
                if model_dropdown.count() > 0:
                    model_dropdown.click()
                    page.wait_for_timeout(1000)
                    target_model = model.lower()
                    target_text = "Nano Banana Pro" if "pro" in target_model else "Nano Banana 2" if "2" in target_model else "Imagen 4" if "imagen" in target_model else model
                    opt = page.locator(f'button:has-text("{target_text}"), [role="option"]:has-text("{target_text}")').first
                    if opt.count() > 0:
                        opt.click(force=True)
                        page.wait_for_timeout(1000)
                    else: page.keyboard.press("Escape")

                # Set Ratio
                if ratio:
                    ratio_btn = page.locator(f'button:has-text("{ratio}"), [role="tab"]:has-text("{ratio}"), [role="button"]:has-text("{ratio}")').first
                    if ratio_btn.count() > 0:
                        ratio_btn.click(force=True)
                        page.wait_for_timeout(1000)

                # Set Count
                target_count_text = f"x{count}"
                count_btn = page.locator(f'button:has-text("{target_count_text}")').first
                if count_btn.count() > 0:
                    count_btn.click(force=True)
                    page.wait_for_timeout(1000)
                
                settings_btn.click() # Close settings
                page.wait_for_timeout(1000)
                page.keyboard.press("Escape")

            # --- Prompt & Generation ---
            prompt_input = page.locator('[role="textbox"]').first
            prompt_input.wait_for(state="visible", timeout=15000)
            
            existing_images = page.locator('img[alt="Generated image"]').all()
            existing_srcs = {img.get_attribute("src") for img in existing_images if img.get_attribute("src")}
            existing_count = len(existing_images)
            
            prompt_input.click()
            page.keyboard.type(prompt, delay=100)
            page.wait_for_timeout(1000)

            # Trigger
            prompt_input.press("Enter")
            logger.info("Pressed Enter. Waiting for generation...")

            # Wait
            try:
                page.locator('text*="Generating", text*="Working", text*="request"').first.wait_for(state="visible", timeout=20000)
                page.locator('text*="Generating", text*="Working", text*="request"').first.wait_for(state="hidden", timeout=240000)
            except:
                try:
                    page.wait_for_function(f"() => document.querySelectorAll('img[alt=\"Generated image\"]').length > {existing_count}", timeout=120000)
                except: pass

            # Download
            if download_dest:
                page.wait_for_timeout(5000)
                all_images = page.locator('img[alt="Generated image"]').all()
                new_results = [img for img in all_images if img.get_attribute("src") not in existing_srcs]
                if not new_results: new_results = all_images[:count]

                is_dir = os.path.isdir(download_dest) if os.path.exists(download_dest) else download_dest.endswith('/')
                for i in range(min(count, len(new_results))):
                    try:
                        new_results[i].click(button="right")
                        page.wait_for_timeout(1500)
                        download_item = page.locator('[role="menuitem"]:has-text("Download"), button:has-text("Download")').first
                        if download_item.count() > 0:
                            download_item.hover()
                            page.wait_for_timeout(1000)
                            target_opt = page.locator('button:has-text("1K"), button:has-text("Original")').first
                            local_path = os.path.join(download_dest, f"result_{i}.png") if is_dir else (f"{os.path.splitext(download_dest)[0]}_{i}{os.path.splitext(download_dest)[1]}" if count > 1 else download_dest)
                            with page.expect_download(timeout=90000) as download_info:
                                if target_opt.count() > 0: target_opt.click()
                                else: download_item.click()
                            download_info.value.save_as(local_path)
                            logger.info(f"Downloaded result {i} to {local_path}")
                    except Exception as e: logger.error(f"Download failed for {i}: {e}")

            browser.close()
    except Exception as e:
        if not isinstance(e, AutomationError): raise AutomationError(f"Generation failed: {e}")
        raise

def create_project_automation(cookie_path: str, name: Optional[str] = None) -> str:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
            _load_cookies(context, cookie_path)
            page = context.new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)
            create_btn = page.locator('button:has-text("New project"), button:has-text("Create")').first
            create_btn.wait_for(state="visible", timeout=10000)
            create_btn.click()
            page.wait_for_url(f"{BASE_URL}/project/**", timeout=30000)
            project_id = page.url.split("/project/")[-1].split("?")[0]
            browser.close()
            return project_id
    except Exception as e: raise AutomationError(f"Failed to create project: {e}")

def list_projects_automation(cookie_path: str) -> List[Dict[str, str]]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
            _load_cookies(context, cookie_path)
            page = context.new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)
            project_links = page.locator('a[href*="/project/"]').all()
            projects = []
            seen_ids = set()
            for link in project_links:
                href = link.get_attribute("href")
                if not href: continue
                project_id = href.split("/project/")[-1].split("?")[0]
                if project_id and project_id not in seen_ids:
                    name = link.inner_text().strip().replace("\n", " ")
                    if not name: name = f"Project {project_id[:8]}"
                    projects.append({"id": project_id, "name": name})
                    seen_ids.add(project_id)
            browser.close()
            return projects
    except Exception as e: raise AutomationError(f"Failed to list projects: {e}")

def list_images_automation(cookie_path: str, project_id: str) -> List[Dict]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
            _load_cookies(context, cookie_path)
            page = context.new_page()
            page.goto(f"{BASE_URL}/project/{project_id}", wait_until="networkidle")
            try: page.locator('img[alt="Generated image"]').first.wait_for(state="visible", timeout=15000)
            except: pass
            image_elements = page.locator('img[alt="Generated image"]').all()
            images = []
            for i, img in enumerate(image_elements):
                src = img.get_attribute("src") or ""
                ref = src.split("name=")[-1] if "name=" in src else f"img_{i}"
                prompt_text = img.get_attribute("aria-label") or img.get_attribute("title") or "No prompt found"
                if prompt_text == "No prompt found":
                    try:
                        card = img.locator('xpath=./ancestor::div[contains(@class, "card") or contains(@style, "background")][1]')
                        if card.count() > 0: prompt_text = card.inner_text().split("\n")[0].strip()
                    except: pass
                images.append({"index": str(i), "ref": ref, "url": src, "prompt": prompt_text})
            browser.close()
            return images
    except Exception as e: raise AutomationError(f"Failed to list images: {e}")

def download_image_automation(cookie_path: str, project_id: str, image_index: str, to_path: str, upscale: str) -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
            _load_cookies(context, cookie_path)
            page = context.new_page()
            page.goto(f"{BASE_URL}/project/{project_id}", wait_until="networkidle")
            try: page.locator('img[alt="Generated image"]').first.wait_for(state="visible", timeout=15000)
            except: pass
            image_elements = page.locator('img[alt="Generated image"]').all()
            idx = int(image_index)
            if idx >= len(image_elements): raise AutomationError(f"Index {idx} out of range.")
            image_elements[idx].click(button="right")
            page.wait_for_timeout(1000)
            download_item = page.locator('[role="menuitem"]:has-text("Download"), button:has-text("Download")').first
            download_item.hover()
            page.wait_for_timeout(1000)
            target_text = "1K" if upscale == "1x" else "2K"
            target_opt = page.locator(f'button:has-text("{target_text}")').first
            with page.expect_download(timeout=90000) as download_info:
                if target_opt.count() > 0: target_opt.click()
                else: download_item.click()
            os.makedirs(os.path.dirname(os.path.abspath(to_path)), exist_ok=True)
            download_info.value.save_as(to_path)
            browser.close()
    except Exception as e: raise AutomationError(f"Failed to download image: {e}")

def verify_auth_automation(cookie_path: str) -> bool:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context()
            _load_cookies(context, cookie_path)
            page = context.new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            try: page.locator('button:has-text("Sign in"), button:has-text("Create")').first.wait_for(state="visible", timeout=10000)
            except: pass
            is_logged_in = "fx/tools/flow" in page.url and not page.locator('button:has-text("Sign in")').is_visible()
            browser.close()
            return is_logged_in
    except: return False

def edit_image_automation(
    cookie_path: str,
    project_id: str,
    image_ref: str,
    prompt: str,
    ratio: str,
    model: str,
    download_dest: Optional[str] = None,
    count: int = 1
) -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            _load_cookies(context, cookie_path)
            page = context.new_page()
            page.goto(f"{BASE_URL}/project/{project_id}", wait_until="networkidle")
            page.wait_for_timeout(5000)
            page.keyboard.press("Escape")

            # --- SETTINGS ---
            settings_btn = page.locator('button:has-text("Nano Banana"), button:has-text("Imagen"), button:has-text("Genie")').first
            if settings_btn.count() > 0:
                settings_btn.click()
                page.wait_for_timeout(2000)
                
                # Model
                model_dropdown = page.locator('button:has-text("arrow_drop_down")').first
                if model_dropdown.count() > 0:
                    model_dropdown.click()
                    page.wait_for_timeout(1000)
                    target_model = model.lower()
                    target_text = "Nano Banana Pro" if "pro" in target_model else "Nano Banana 2" if "2" in target_model else "Imagen 4" if "imagen" in target_model else model
                    opt = page.locator(f'button:has-text("{target_text}"), [role="option"]:has-text("{target_text}")').first
                    if opt.count() > 0:
                        opt.click(force=True)
                        page.wait_for_timeout(1000)
                    else: page.keyboard.press("Escape")

                # Ratio
                if ratio:
                    ratio_btn = page.locator(f'button:has-text("{ratio}"), [role="tab"]:has-text("{ratio}"), [role="button"]:has-text("{ratio}")').first
                    if ratio_btn.count() > 0:
                        ratio_btn.click(force=True)
                        page.wait_for_timeout(1000)

                # Count
                target_count_text = f"x{count}"
                count_btn = page.locator(f'button:has-text("{target_count_text}")').first
                if count_btn.count() > 0:
                    count_btn.click(force=True)
                    page.wait_for_timeout(1000)
                
                settings_btn.click()
                page.wait_for_timeout(1000)
                # Removed the aggressive Escape here that might be hiding the prompt bar

            # Blacklist existing images
            initial_srcs = {img.get_attribute("src") for img in page.locator('img[alt="Generated image"]').all() if img.get_attribute("src")}

            # --- ATTACHMENT ---
            if os.path.isfile(image_ref):
                logger.info(f"Uploading file via Plus menu: {image_ref}")
                
                # 1. Capture initial count BEFORE upload
                initial_count = page.locator('img[alt="Generated image"]').count()
                
                # 2. Click Plus button and Upload
                page.locator('button:has(i:has-text("add_2"))').first.click()
                page.wait_for_timeout(2000)
                
                # Click Upload
                upload_target = page.locator('div[data-radix-popper-content-wrapper] div:has-text("Upload image")').last
                with page.expect_file_chooser() as fc_info:
                    upload_target.click()
                fc_info.value.set_files(image_ref)
                
                # 3. CRITICAL: Wait for image count to increase BY 1
                logger.info("Waiting for asset to fully attach to project...")
                try:
                    page.wait_for_function(
                        f"() => document.querySelectorAll('img[alt=\"Generated image\"]').length > {initial_count}",
                        timeout=60000
                    )
                    attached_count = page.locator('img[alt="Generated image"]').count()
                    logger.info(f"Asset attached successfully. New count: {attached_count} (Expected: {initial_count + 1})")
                except Exception as e:
                    logger.warning(f"Timed out waiting for asset attachment: {e}")
                page.wait_for_timeout(3000)
            else:

                # [Selecting from project via Plus Menu]
                idx = int(image_ref)
                page.locator('button:has(i:has-text("add_2"))').first.click()
                page.wait_for_timeout(3000)
                recent_imgs = page.locator('div[data-radix-popper-content-wrapper] [data-known-size] img').all()
                if idx < len(recent_imgs):
                    recent_imgs[idx].click()
                else:
                    page.keyboard.press("Escape")
                    image_elements = page.locator('img[alt="Generated image"]').all()
                    image_elements[idx].click()
                    page.locator('button:has-text("Create"), button:has-text("arrow_forward")').last.click()


            # --- PRE-GENERATION STATE ---
            # Capture everything now, including the newly attached asset
            final_pre_gen_images = page.locator('img[alt="Generated image"]').all()
            final_blacklist = {img.get_attribute("src") for img in final_pre_gen_images if img.get_attribute("src")}
            existing_count = len(final_pre_gen_images)
            logger.info(f"Blacklisted {existing_count} images (incl. uploaded asset).")

            # --- PROMPT ---
            prompt_input = page.locator('[role="textbox"]').first
            prompt_input.wait_for(state="visible", timeout=15000)
            prompt_input.click()
            page.keyboard.type(prompt, delay=100)
            page.wait_for_timeout(1000)
            prompt_input.press("Enter")
            logger.info("Triggered generation with Enter. Waiting...")

            # --- WAIT ---
            try:
                # Fixed selector syntax: use :has-text() instead of text*=
                page.locator(':has-text("Generating"), :has-text("Working"), :has-text("request")').first.wait_for(state="visible", timeout=20000)
                page.locator(':has-text("Generating"), :has-text("Working"), :has-text("request")').first.wait_for(state="hidden", timeout=240000)
                logger.info("Generation indicator detected and completed.")
            except:
                logger.info("No generation indicator found, waiting for image count increase...")
                try:
                    page.wait_for_function(f"() => {{ const c = document.querySelectorAll('img[alt=\"Generated image\"]').length; return c > {existing_count}; }}", timeout=120000)
                    logger.info("Image count increased successfully.")
                except:
                    logger.warning("Count wait also failed. Proceeding to download anyway.")
            
            # --- DOWNLOAD ---
            if download_dest:
                # CRITICAL: Re-scan the gallery AFTER generation completes
                # The newly generated image appears at the TOP (index 0) of the gallery
                logger.info("Re-scanning gallery for newly generated images...")
                page.wait_for_timeout(5000)
                
                # Get ALL images currently in the project gallery
                all_images = page.locator('img[alt="Generated image"]').all()
                logger.info(f"Found {len(all_images)} total images in gallery")
                
                # The NEWEST generated images are at the TOP of the gallery (index 0, 1, 2...)
                # We want the first 'count' images which are the newly generated ones
                new_results = all_images[:count]
                
                if not new_results:
                    logger.error("No images found in gallery to download!")
                    raise AutomationError("No images found to download")
                
                logger.info(f"Downloading {len(new_results)} newly generated image(s) from top of gallery")
                
                is_dir = os.path.isdir(download_dest) if os.path.exists(download_dest) else download_dest.endswith('/')
                for i in range(min(count, len(new_results))):
                    try:
                        new_results[i].click(button="right")
                        page.wait_for_timeout(1500)
                        download_item = page.locator('[role="menuitem"]:has-text("Download"), button:has-text("Download")').first
                        if download_item.count() > 0:
                            download_item.hover()
                            page.wait_for_timeout(1000)
                            target_opt = page.locator('button:has-text("1K"), button:has-text("Original")').first
                            local_path = os.path.join(download_dest, f"edited_{i}.png") if is_dir else (f"{os.path.splitext(download_dest)[0]}_{i}{os.path.splitext(download_dest)[1]}" if count > 1 else download_dest)
                            with page.expect_download(timeout=90000) as download_info:
                                if target_opt.count() > 0: target_opt.click()
                                else: download_item.click()
                            download_info.value.save_as(local_path)
                            logger.info(f"Downloaded NEW result {i} to {local_path}")
                    except Exception as e: logger.error(f"Download failed: {e}")

            browser.close()
    except Exception as e: raise AutomationError(f"Edit failed: {e}")
