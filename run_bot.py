# ==============================================================================
#                  GEMINI WEB AUTOMATION & IMAGE GENERATION BOT
# ==============================================================================
# Description: Automates batch image processing (uploading images, sending prompts,
#              and downloading the results) via the Gemini Advanced web interface
#              (gemini.google.com) using your logged-in Google profile.
# Resiliency:  Includes automatic navigation retries, CORS bypass, canvas extraction,
#              and HEIC photo sorting.
#
# How to run:
#   1. Close all active instances of Google Chrome.
#   2. Open CMD and run:
#      start chrome --remote-debugging-port=9222 --profile-directory="Default"
#   3. Place your images to process in:
#      E:\MySaasProjects\gemini-image-generator-bot\input_images\
#   4. Run this script:
#      python run_bot.py
# ==============================================================================

import os
import sys
import time
import json
import shutil
import io
import mimetypes
import base64
import tempfile
import requests
import re
import random
from playwright.sync_api import sync_playwright

# ------------------------------------------------------------------------------
# DEFAULT CONFIGURATION
# ------------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "source_folder": "E:\\MySaasProjects\\gemini-image-generator-bot\\input_images",
    "destination_folder": "E:\\MySaasProjects\\gemini-image-generator-bot\\output_images",
    "prompt": "REMOVE THE BACKGROUND OF THE IMAGE AND MAKE IT TRANSPARENT WITH A WHITE BACKGROUND ",
    "use_shuffled_prompts": True,
    "chrome_mode": "persistent",
    "chrome_cdp_url": "http://127.0.0.1:9222",
    "chrome_profile_path": "C:\\Users\\DELL\\AppData\\Local\\Google\\Chrome\\User Data",
    "chrome_profile_name": "Default",
    "gemini_url": "https://gemini.google.com/app",
    "delay_between_generations_sec": 10,
    "skip_already_processed": True
}

PREMIUM_PROMPTS = [
    "Top-down flat lay, expert product photography of a [dress description] on a rich champagne gold satin silk background. Delicate white gypsophila (baby's breath) floral clusters in opposing corners, traditional polished brass bowl in the top right. Specifications: Focus on high-contrast zardozi threadwork, gold foil sheen, and tactile sequin reflections. Soft, diffused studio lighting. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k resolution. --ar 1:1",
    "Overhead flat lay, realistic commercial design. The [dress description] placed centrally on folded champagne gold satin silk. Accentuated by a scattering of real freshwater pearls and delicate white baby's breath. Focus: embroidery tension, fine netting sheen, intricate thread work. Gentle, soft, airy diffused lighting. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, photorealistic, premium feel. --ar 1:1",
    "Premium commercial product photograph, overhead perspective. The [dress description] on folded champagne gold satin. Framed by vivid pink gerbera daisies, loose fuchsia rose petals, and a polished brass bowl top right. Focus points: precise border stitching on traditional paisley motifs, gold thread relief, realistic jewel reflections, high color saturation. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k resolution, crisp details. --ar 1:1",
    "Flat lay, high-fashion textile focus. The [dress description] centered on champagne gold satin. Bordered by pink gerbera daisies. Technical focus: sharp definition of geometric thread work, realistic multi-faceted bead reflections, deep saturated purples and blues. Crisp, clean commercial lighting with sharp definition. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, hyper-detailed. --ar 1:1",
    "Commercial flat lay of a [dress description] on champagne gold satin silk. Accentuated by vivid pink gerbera daisies and a polished brass bowl. Specifics: hyper-realistic dense bead textures, clean circular motifs, contrasting embroidery (pink, yellow, navy blue). Soft lighting highlighting the 3D surface of the beads. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, photorealistic. --ar 1:1",
    "Expert product flat lay photography. The [dress description] centrally placed on folded champagne gold satin silk. Framed by contrasting lavender and deep purple chrysanthemums and a brass bowl. Focus: High definition of diamond and teardrop motifs, contrasting neon thread saturation, sharp beadwork. Crisp, commercial studio lighting. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k. --ar 1:1",
    "Overhead photo of a [dress description] on luxury champagne gold satin silk. Features: Traditional floral motifs, sharp contrast between pastel base and neon thread details. Accented by purple chrysanthemums and baby's breath. Real-world texture of fabric weaves and heavy embroidery. Soft, flattering studio light. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k. --ar 1:1",
    "Expert top-down flat lay, premium marketing shot. The [dress description] on folded champagne gold satin silk. Specific radial sunburst design with red and purple alternating rays and teardrop petal borders. Specifications: precise thread-to-thread definition, realistic gold zari relief, rich velvet texture simulation, natural light falloff. Background: Baby's breath, rose petals, and brass bowl. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, high fidelity. --ar 1:1",
    "Photorealistic overhead product shot of a [dress description] on rich gold satin. Features a traditional mandala burst design, zardozi gold border, multi-color petals (red, purple). Background: Rose petals and pink gerbera daisies. Emphasis on realistic thread tension and fabric weave. Balanced, professional lighting. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k resolution. --ar 1:1",
    "Clean, modern commercial flat lay. The [dress description] on textured champagne gold satin. Framed only by loose white pearls, small silver sequins, and subtle gypsophila (baby's breath). Specifics: Focus on subtle tone-on-tone embroidery, delicate sheen of fine fabrics. Elegant, clean aesthetic. Pure white, airy light. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, photorealistic. --ar 1:1",
    "High-end flat lay photography. A [dress description] on rich, folded champagne gold satin. Framed by white chrysanthemums and multiple polished brass containers. Specifics: Deep fabric weave definition, hyper-realistic metallic thread reflectivity, crisp beadwork. Strong use of rim lighting to separate subject from background. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, photorealistic. --ar 1:1",
    "Realistic top-down product photography. The [dress description] centered on champagne gold satin. Ambient light (simulating natural window light) creates soft shadows and gentle highlights. Minimal props: small white flowers and a subtle brass bowl. Textures: tactile softness of silk, defined zardozi threads. Calm, premium atmosphere. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k. --ar 1:1",
    "Overhead flat lay photography of a [dress description] on champagne gold satin silk. Features: heavy zardozi, mirror-work, and sequin elements. Lighting: Dynamic studio setup designed to maximize specular reflections on mirrors and metallic threads. Background props: baby's breath and a dark patina brass bowl. Sharp focus, maximum clarity. At the bottom center of the image, below the dress, render the text 'Shiv Kripa' in a clean, elegant, luxury serif branding font (delicate and small, approximately 8% to 10% of the image width) with a thin horizontal separator line and a small floral/diamond motif accent in the middle, matching the color theme of the dress. 8k, photorealistic. --ar 1:1"
]

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.heic', '.heif')

def get_dress_description(filename):
    """Helper to extract a descriptive name from the image filename.
    Falls back to 'luxury designer dress' if filename is generic (e.g. IMG_0250).
    """
    base_name, _ = os.path.splitext(filename)
    # Check if the filename is generic (IMG_XXXX, PHOTO_XXXX, numbers, or UUIDs)
    if re.match(r'^(IMG_|DSC_|PHOTO_|\d{4,})', base_name, re.IGNORECASE) or (len(base_name) > 20 and '-' in base_name):
        return "luxury designer dress"
    
    # Replace underscores/hyphens/spaces with single space
    cleaned = re.sub(r'[-_\s\.]+', ' ', base_name).strip()
    if not cleaned or len(cleaned) < 2:
        return "luxury designer dress"
    return cleaned

def load_config():
    """Loads configuration from config.json if available, otherwise falls back to defaults."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge loaded config with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"Warning: Failed to load config.json ({e}). Using defaults.")
    return DEFAULT_CONFIG
from telegram_status import BotState, send_notification, check_telegram_status_requests

# ------------------------------------------------------------------------------
# DRIVE & FILE HANDLER
# ------------------------------------------------------------------------------
import hashlib

def get_file_hash(file_path):
    """Calculates MD5 hash of a file to check for content modifications, bypassing time discrepancy bugs."""
    hasher = hashlib.md5()
    try:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return ""

# ------------------------------------------------------------------------------
# DRIVE & FILE HANDLER
# ------------------------------------------------------------------------------
class DriveHandler:
    def __init__(self, config):
        self.config = config
        self.source_folder = config.get("source_folder")
        self.destination_folder = config.get("destination_folder")
        self.metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed_metadata.json')
        self.metadata = self.load_metadata()
        
        # Ensure directories exist
        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(self.destination_folder, exist_ok=True)

    def load_metadata(self):
        """Loads processed images metadata (file hashes)."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_metadata(self):
        """Saves processed images metadata (file hashes)."""
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save processed_metadata.json ({e})")

    def get_input_images(self):
        """Returns input images sorted chronologically by click time."""
        images = []
        if not os.path.exists(self.source_folder):
            print(f"[-] Source folder {self.source_folder} does not exist.")
            return []
        
        # Scan folder and gather timestamps
        file_list = []
        for f in os.listdir(self.source_folder):
            if f.lower().endswith(IMAGE_EXTENSIONS):
                # Ignore generated files that were accidentally copied back to the input folder
                if "_gen_" in f:
                    continue
                file_path = os.path.join(self.source_folder, f)
                file_list.append((f, file_path, os.path.getmtime(file_path)))
        
        # Sort oldest first (chronological order)
        file_list.sort(key=lambda x: x[2])
        
        for f, file_path, _ in file_list:
            images.append({
                'name': f,
                'path': file_path
            })
        return images

    def check_if_already_processed(self, input_filename):
        """Checks if files matching output file name already exist in output folder.
        Uses MD5 content hashing to detect when the original image is recopied/updated,
        deleting the old output and scheduling a fresh recreation.
        Also prevents duplicate content (same image with a different name) from being processed twice.
        """
        base_name, _ = os.path.splitext(input_filename)
        if not os.path.exists(self.destination_folder):
            return False
            
        input_path = os.path.join(self.source_folder, input_filename)
        if not os.path.exists(input_path):
            return False
            
        current_hash = get_file_hash(input_path)
        if not current_hash:
            return False
            
        # 1. Duplicate Content Check: If this exact image content (hash) was already processed
        # under ANY filename, and that output file exists, we should skip it to avoid generating twice!
        for name, h in self.metadata.items():
            if h == current_hash and name != input_filename:
                # Check if the output for the other file exists
                other_base, _ = os.path.splitext(name)
                other_output_exists = False
                for f in os.listdir(self.destination_folder):
                    if f.startswith(other_base) and f.lower().endswith(IMAGE_EXTENSIONS) and "gen" in f:
                        other_output_exists = True
                        break
                if other_output_exists:
                    print(f"  - [Skipped] '{input_filename}' contains identical image content to already processed '{name}'. Skipping duplicate.")
                    return True
            
        # 2. Get matching outputs for current filename
        has_output = False
        for f in os.listdir(self.destination_folder):
            if f.startswith(base_name) and f.lower().endswith(IMAGE_EXTENSIONS) and "gen" in f:
                has_output = True
                break
                
        # If output files exist, check if input content changed via MD5
        if has_output:
            stored_hash = self.metadata.get(input_filename)
            
            # If we don't have a stored hash but output exists, store it
            if not stored_hash:
                self.metadata[input_filename] = current_hash
                self.save_metadata()
                return True # Output is up to date, skip
                
            # If the user recopied/changed the input file, the hashes will not match!
            if current_hash != stored_hash:
                print(f"[i] Input file '{input_filename}' content has been updated/recopied. Triggering re-processing...")
                # Delete outdated output files
                for f in os.listdir(self.destination_folder):
                    if f.startswith(base_name) and f.lower().endswith(IMAGE_EXTENSIONS) and "gen" in f:
                        try:
                            os.remove(os.path.join(self.destination_folder, f))
                            print(f"  - Deleted outdated output file: {f}")
                        except Exception as e:
                            print(f"  - Warning: Could not delete outdated output: {e}")
                return False  # Do not skip, process it!
            return True  # Output is up to date, skip
            
        return False

    def save_outputs(self, input_filename, temp_image_paths):
        """Saves generated images, copies original file timestamps, and updates file hash metadata."""
        base_name, _ = os.path.splitext(input_filename)
        saved_paths = []
        
        for i, temp_path in enumerate(temp_image_paths):
            ext = os.path.splitext(temp_path)[1]
            dest_filename = f"{base_name}_gen_{i+1}{ext}"
            dest_path = os.path.join(self.destination_folder, dest_filename)
            shutil.copy(temp_path, dest_path)
            print(f"[+] Saved generated image: {dest_path}")
            saved_paths.append(dest_path)
            
            # Preserve original timestamp (clicked date)
            try:
                orig_path = os.path.join(self.source_folder, input_filename)
                if os.path.exists(orig_path):
                    orig_mtime = os.path.getmtime(orig_path)
                    orig_atime = os.path.getatime(orig_path)
                    os.utime(dest_path, (orig_atime, orig_mtime))
                    print("  - Original timestamp applied successfully.")
            except Exception as e:
                print(f"  - Warning: Failed to set original file timestamp: {e}")
                
        # Save input file hash to metadata to prevent redundant processing
        try:
            orig_path = os.path.join(self.source_folder, input_filename)
            current_hash = get_file_hash(orig_path)
            if current_hash:
                self.metadata[input_filename] = current_hash
                self.save_metadata()
        except Exception as e:
            print(f"Warning: Failed to save file hash metadata: {e}")
            
        return saved_paths

# ------------------------------------------------------------------------------
# GEMINI PLAYWRIGHT AUTOMATION
# ------------------------------------------------------------------------------
class GeminiAutomation:
    def __init__(self, config):
        self.config = config
        self.chrome_mode = config.get("chrome_mode", "persistent").lower()
        self.chrome_cdp_url = config.get("chrome_cdp_url", "http://127.0.0.1:9222")
        self.chrome_profile_path = config.get("chrome_profile_path")
        self.chrome_profile_name = config.get("chrome_profile_name", "Default")
        self.gemini_url = config.get("gemini_url", "https://gemini.google.com/app")
        
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Launches or connects to Chrome."""
        self.playwright = sync_playwright().start()
        
        if self.chrome_mode == "cdp":
            print(f"[i] Connecting to existing Chrome instance via CDP at {self.chrome_cdp_url}...")
            try:
                self.browser = self.playwright.chromium.connect_over_cdp(self.chrome_cdp_url)
                if len(self.browser.contexts) > 0:
                    self.context = self.browser.contexts[0]
                    if len(self.context.pages) > 0:
                        self.page = self.context.pages[0]
                
                if not self.page:
                    if not self.context:
                        self.context = self.browser.new_context()
                    self.page = self.context.new_page()
                print("[+] Successfully connected to existing Chrome browser.")
            except Exception as e:
                raise ConnectionError(
                    f"Failed to connect to Chrome at {self.chrome_cdp_url}.\n"
                    f"Error: {e}\n"
                    "Make sure Chrome is running with remote debugging enabled. E.g.:\n"
                    "chrome.exe --remote-debugging-port=9222"
                )
        else:
            # Persistent Profile Mode
            profile_dir = os.path.join(self.chrome_profile_path, self.chrome_profile_name)
            print(f"[i] Launching Chrome with persistent profile at {profile_dir}...")
            
            # Kill conflicts
            try:
                os.system("taskkill /F /IM chrome.exe >nul 2>&1")
            except Exception:
                pass
                
            try:
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    channel='chrome',
                    headless=False,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars"
                    ]
                )
                self.page = self.context.pages[0] if len(self.context.pages) > 0 else self.context.new_page()
                print("[+] Successfully launched Chrome instance automatically.")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to launch Chrome with profile directory. Error: {e}\n"
                    "Make sure all other Chrome windows are closed before running, "
                    "or run Chrome manually with --remote-debugging-port=9222 and switch config to 'cdp'."
                )

    def safe_goto(self, url, retries=3):
        """Resilient page navigation with network retries."""
        for attempt in range(retries):
            try:
                print(f"[i] Navigating to {url} (Attempt {attempt+1}/{retries})...")
                self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self.page.wait_for_timeout(2000)
                return True
            except Exception as e:
                print(f"[-] Navigation attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    self.page.wait_for_timeout(4000)
        raise RuntimeError(f"Failed to navigate to {url} after {retries} attempts.")

    def safe_download(self, url, dest_path, canvas_base64=None, retries=3):
        """Resilient image downloader (bypasses CORS using Python requests)."""
        if canvas_base64:
            try:
                image_bytes = base64.b64decode(canvas_base64)
                with open(dest_path, 'wb') as f:
                    f.write(image_bytes)
                return True
            except Exception as e:
                print(f"[-] Failed saving canvas image: {e}. Retrying via fetch...")

        for attempt in range(retries):
            try:
                if url.startswith("blob:"):
                    base64_data = self.page.evaluate("""
                        async (srcUrl) => {
                            const response = await fetch(srcUrl);
                            const blob = await response.blob();
                            return new Promise((resolve, reject) => {
                                const reader = new FileReader();
                                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                                reader.onerror = reject;
                                reader.readAsDataURL(blob);
                            });
                        }
                    """, url)
                    image_bytes = base64.b64decode(base64_data)
                    with open(dest_path, 'wb') as f:
                        f.write(image_bytes)
                    return True
                else:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        with open(dest_path, 'wb') as f:
                            f.write(response.content)
                        return True
                    else:
                        raise RuntimeError(f"HTTP {response.status_code}")
            except Exception as e:
                print(f"[-] Download attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(3)
        raise RuntimeError(f"Failed to download image from {url} after {retries} attempts.")

    def verify_login(self):
        """Verifies if Chrome is logged in to Gemini."""
        self.safe_goto(self.gemini_url)
        textbox = self.page.locator(
            '.ql-editor[contenteditable="true"], '
            '[role="textbox"], '
            'textarea, '
            'input[type="text"]'
        ).first
        
        if textbox.count() == 0:
            print("\n" + "="*60)
            print("WARNING: Gemini chat textbox not found. You might not be logged in.")
            print("Please log in to your Google Account on the opened Chrome window.")
            print("Once you are logged in and see the Gemini chat interface, press Enter in this console...")
            print("="*60 + "\n")
            input("Press Enter to continue after logging in...")
            self.safe_goto(self.gemini_url)
            if textbox.count() == 0:
                print("[-] Still not logged in. Trying to proceed anyway...")
            print("[+] Verified: Logged in and prompt input area found.")
            
    def start_new_chat(self):
        """Starts a fresh new chat session to clear DOM memory and optimize tokens."""
        print("[i] Cleaning up memory and starting a fresh chat session...")
        self.safe_goto(self.gemini_url)
        textbox_selector = (
            '.ql-editor[contenteditable="true"], '
            '[role="textbox"], '
            'textarea, '
            'input[type="text"]'
        )
        textbox = self.page.locator(textbox_selector).last
        textbox.wait_for(state="visible", timeout=30000)

    def run_generation(self, image_path, prompt):
        """Uploads image, submits prompt, and extracts results in the same chat session."""
        # Ensure previous message has fully finished generating before proceeding
        print("[i] Checking if Gemini is busy generating...")
        stop_btn_selectors = [
            'button[aria-label*="Stop" i]',
            'button:has(svg[path*="stop" i])',
            '[aria-label*="Stop generating" i]',
            'button:has-text("Stop")'
        ]
        
        is_generating = True
        while is_generating:
            found_stop = False
            for sel in stop_btn_selectors:
                try:
                    btn = self.page.locator(sel).last
                    if btn.count() > 0 and btn.is_visible():
                        found_stop = True
                        break
                except Exception:
                    pass
            
            if found_stop:
                print("[i] Gemini is still generating the previous response. Waiting 5 seconds...")
                self.page.wait_for_timeout(5000)
            else:
                is_generating = False
                
        print("[+] Gemini is ready. Starting next image process...")
        # Wait for textbox
        textbox_selector = (
            '.ql-editor[contenteditable="true"], '
            '[role="textbox"], '
            'textarea, '
            'input[type="text"]'
        )
        textbox = self.page.locator(textbox_selector).last
        textbox.wait_for(state="visible", timeout=30000)
        textbox.focus()
        
        # Wait for any active uploads or loading spinners on the page to disappear (handles slow internet lag)
        loading_selectors = [
            'mat-progress-bar',
            '.progress-bar',
            '.upload-progress',
            '.loading-spinner',
            'circle-loader'
        ]
        for sel in loading_selectors:
            try:
                loader = self.page.locator(sel).last
                if loader.count() > 0 and loader.is_visible():
                    print("[i] Slow internet detected: waiting for previous upload/loading indicator to finish...")
                    loader.wait_for(state="hidden", timeout=30000)
            except Exception:
                pass
                
        # Clean up any stuck/existing upload attachments in the input area
        print("[i] Checking for any stuck attachments in the input area...")
        clear_btn_selectors = [
            'button[aria-label*="Remove" i]',
            'button[aria-label*="Delete" i]',
            'button[aria-label*="Clear" i]',
            '.remove-button',
            '.clear-button',
            'button:has(svg[path*="close" i])'
        ]
        
        # Only check inside the active input area container
        input_container_selectors = [
            '.chat-input-container',
            '.textarea-wrapper',
            '.input-area-container',
            '.input-container',
            'form'
        ]
        input_container = None
        for container_sel in input_container_selectors:
            try:
                loc = self.page.locator(container_sel).last
                if loc.count() > 0:
                    input_container = loc
                    break
            except Exception:
                pass
                
        if input_container:
            for sel in clear_btn_selectors:
                try:
                    btn = input_container.locator(sel).last
                    if btn.count() > 0 and btn.is_visible():
                        print("[+] Found a stuck image attachment from a previous slow upload. Clearing it...")
                        btn.click(timeout=3000)
                        self.page.wait_for_timeout(1000)
                except Exception:
                    pass
        
        # Auto-orient the image before uploading (rotates landscape upright if shot vertically)
        upload_path = image_path
        temp_oriented_file = None
        
        try:
            from PIL import Image, ImageOps
            import pillow_heif
            
            # Register HEIF opener with Pillow
            pillow_heif.register_heif_opener()
            
            print(f"[i] Checking image orientation for: {image_path}...")
            img_obj = Image.open(image_path)
            
            # Transpose based on EXIF orientation
            oriented_img = ImageOps.exif_transpose(img_obj)
            
            # Check if transpose actually changed something, or if it is a HEIC file 
            # (which we want to convert to PNG/JPG for absolute safety in Chrome upload)
            is_heic = image_path.lower().endswith(('.heic', '.heif'))
            orientation_changed = (img_obj.size != oriented_img.size)
            
            if is_heic or orientation_changed:
                fd, temp_oriented_file = tempfile.mkstemp(suffix=".jpg")
                os.close(fd)
                
                # Convert to RGB (required for JPEG)
                if oriented_img.mode in ("RGBA", "P"):
                    oriented_img = oriented_img.convert("RGB")
                    
                oriented_img.save(temp_oriented_file, "JPEG", quality=95)
                upload_path = temp_oriented_file
                if orientation_changed:
                    print(f"[+] Sideways/landscape orientation detected. Auto-rotated straight!")
                else:
                    print(f"[+] Converted HEIC to standard JPEG for upload compatibility.")
        except Exception as e:
            print(f"  - Warning: Failed to check or auto-rotate image orientation: {e}")
        
        # Upload Image
        if upload_path and os.path.exists(upload_path):
            print(f"[i] Uploading image: {image_path}...")
            uploaded = False
            
            # Step A: Click upload button to mount menu/input
            try:
                upload_btn = self.page.locator(
                    'button[aria-label*="Add files" i], '
                    'button[aria-label*="Upload" i], '
                    '[aria-label*="Add files" i], '
                    '[aria-label*="Upload" i], '
                    'button:has-text("Add files"), '
                    'button:has-text("Upload")'
                ).last
                upload_btn.wait_for(state="attached", timeout=5000)
                upload_btn.click(timeout=5000, no_wait_after=True)
                self.page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  - Warning: Failed to click upload button: {e}")
                
            # Step B: Click menu option and intercept FileChooser (Natively opens upload dialog, most reliable)
            try:
                menu_selectors = [
                    'span:has-text("Upload files")',
                    'span:has-text("Upload from computer")',
                    'span:has-text("computer")',
                    '[aria-label*="Upload from computer" i]',
                    '[aria-label*="Upload files" i]',
                    'button:has-text("Upload")',
                    'text="Upload from computer"',
                    'text="Upload files"'
                ]
                menu_item = None
                for sel in menu_selectors:
                    try:
                        loc = self.page.locator(sel).last
                        if loc.count() > 0 and loc.is_visible():
                            menu_item = loc
                            break
                    except Exception:
                        pass
                        
                if menu_item:
                    with self.page.expect_file_chooser(timeout=5000) as fc_info:
                        menu_item.click(timeout=5000, no_wait_after=True)
                    file_chooser = fc_info.value
                    file_chooser.set_files(upload_path)
                    print("[+] Image successfully uploaded via menu FileChooser.")
                    self.page.wait_for_timeout(3000)
                    uploaded = True
            except Exception as e2:
                print(f"  - Warning: FileChooser upload failed: {e2}")
                
            # Step C: Fallback to direct input injection if FileChooser failed
            if not uploaded:
                try:
                    file_input = self.page.locator('input[type="file"]').last
                    if file_input.count() > 0:
                        file_input.set_input_files(upload_path, timeout=5000)
                        print("[+] Image successfully uploaded via direct input injection fallback.")
                        self.page.wait_for_timeout(3000)
                        uploaded = True
                except Exception as e3:
                    print(f"  - Warning: Direct input injection fallback failed: {e3}")
                    
            if not uploaded:
                raise RuntimeError(f"Failed to upload image '{image_path}' after trying FileChooser and direct input injection. Stopping execution for this image.")
        
        # Submit Prompt
        print(f"[i] Submitting prompt: '{prompt}'")
        textbox.fill(prompt)
        self.page.wait_for_timeout(1000)
        
        send_btn_selectors = (
            'button[aria-label*="Send" i], '
            '[aria-label*="Send message" i], '
            'button:has(svg[path*="send" i]), '
            'button:has-text("Send"), '
            '[aria-label="Submit"]'
        )
        send_btn = self.page.locator(send_btn_selectors).last
        
        # Wait for the Send button to become visible
        try:
            send_btn.wait_for(state="visible", timeout=15000)
        except Exception:
            pass
            
        # Wait up to 20 seconds for the image upload processing in the input box to finish (Send button becomes enabled)
        print("[i] Waiting for image upload processing in the input area to finish...")
        for upload_wait in range(20):
            if send_btn.count() > 0 and send_btn.is_enabled() and not send_btn.get_attribute("disabled"):
                break
            self.page.wait_for_timeout(1000)
            
        # Send message with verification
        sent = False
        for send_attempt in range(3):
            try:
                # If Send button is enabled, click it
                if send_btn.count() > 0 and send_btn.is_visible() and send_btn.is_enabled() and not send_btn.get_attribute("disabled"):
                    send_btn.click(timeout=5000, no_wait_after=True)
                else:
                    textbox.focus()
                    textbox.press("Enter")
                
                # Verify send: wait up to 4 seconds for textbox value to clear
                self.page.wait_for_timeout(2000)
                textbox_val = ""
                try:
                    textbox_val = textbox.input_value()
                except Exception:
                    try:
                        textbox_val = self.page.evaluate("el => el.textContent", textbox.element_handle())
                    except Exception:
                        pass
                
                if not textbox_val or not textbox_val.strip():
                    sent = True
                    print("[+] Message sent successfully.")
                    break
            except Exception as e:
                print(f"  - Send attempt {send_attempt+1} warning: {e}")
            
            # If not verified, try fallback press Enter
            print("[i] Send verification failed (text still in input box). Pressing Enter as fallback...")
            try:
                textbox.focus()
                textbox.press("Enter")
                self.page.wait_for_timeout(2000)
            except Exception:
                pass
                
        if not sent:
            print("[-] Warning: Send verification timed out. Proceeding to wait for response...")
        
        print("[i] Waiting for response to complete (up to 3 minutes)...")
        
        # Wait for Thumbs-Up button
        good_response_btn = self.page.locator(
            'button[aria-label*="Good response" i], '
            'button[aria-label*="Like" i], '
            '[aria-label*="Good response" i], '
            '[aria-label*="Like" i], '
            '.response-actions, '
            '.message-actions-container'
        ).last
        
        try:
            good_response_btn.wait_for(state="visible", timeout=180000)
            print("[+] Response completed successfully.")
            self.page.wait_for_timeout(5000) # stabilizing time for images
        except Exception:
            print("[-] Warning: Response completion indicator not found. Extracting anyway...")
            
        # Extract images using Canvas inside browser to bypass CORS
        image_data = self.page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button[aria-label*="Good response"], button[aria-label*="Like"], .response-actions');
                if (btns.length === 0) return [];
                const lastBtn = btns[btns.length - 1];
                
                let container = lastBtn.parentElement;
                while (container && container.tagName !== 'BODY') {
                    const imgs = container.querySelectorAll('img');
                    const validImgs = [];
                    for (const img of imgs) {
                        // Exclude original uploaded photos (which exist in user queries, attachment previews, or chat input)
                        if (img.closest('user-query, .query-content, .user-message, .input-image, .attachment-preview, g-image-attachment, .chat-input-container, .user-query, [role="presentation"] .image-preview, .upload-preview')) {
                            continue;
                        }
                        const width = img.naturalWidth || img.width || 0;
                        const height = img.naturalHeight || img.height || 0;
                        if (width > 100 && height > 100) {
                            validImgs.push(img);
                        }
                    }
                    if (validImgs.length > 0) {
                        return validImgs.map(img => {
                            try {
                                const canvas = document.createElement('canvas');
                                canvas.width = img.naturalWidth || img.width;
                                canvas.height = img.naturalHeight || img.height;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                return {
                                    src: img.src,
                                    base64: canvas.toDataURL('image/png').split(',')[1],
                                    error: null
                                };
                            } catch (err) {
                                return {
                                    src: img.src,
                                    base64: null,
                                    error: err.toString()
                                };
                            }
                        });
                    }
                    container = container.parentElement;
                }
                return [];
            }
        """)
        
        if not image_data:
            print("[-] No generated images found in this response. Checking for rate limit messages...")
            latest_response_text = ""
            try:
                latest_response_text = self.page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('button[aria-label*="Good response"], button[aria-label*="Like"], .response-actions');
                        if (btns.length === 0) return "";
                        const lastBtn = btns[btns.length - 1];
                        let container = lastBtn.parentElement;
                        while (container && container.tagName !== 'BODY') {
                            if (container.classList.contains('message-content') || container.tagName === 'MESSAGE-CONTENT') {
                                return container.textContent;
                            }
                            container = container.parentElement;
                        }
                        return lastBtn.parentElement ? lastBtn.parentElement.textContent : "";
                    }
                """)
            except Exception:
                pass
                
            rate_limit_keywords = [
                "create more images than usual",
                "can't do that for you right now",
                "ask me again later",
                "reached your limit",
                "generation limit",
                "too many images",
                "try again later"
            ]
            
            for keyword in rate_limit_keywords:
                if keyword.lower() in latest_response_text.lower():
                    if temp_oriented_file and os.path.exists(temp_oriented_file):
                        try: os.remove(temp_oriented_file)
                        except Exception: pass
                    raise RuntimeError("GEMINI_RATE_LIMIT_REACHED: Gemini is rate-limiting image generation right now.")
                    
            # Clean up temp oriented image if exists
            if temp_oriented_file and os.path.exists(temp_oriented_file):
                try: os.remove(temp_oriented_file)
                except Exception: pass
            return []
            
        print(f"[i] Found {len(image_data)} generated image(s). Downloading...")
        
        # Download images
        temp_paths = []
        for i, item in enumerate(image_data):
            try:
                fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                self.safe_download(item['src'], temp_path, canvas_base64=item['base64'])
                temp_paths.append(temp_path)
            except Exception as e:
                print(f"[-] Failed to download image {i+1}: {e}")
                
        # Clean up temp oriented image if exists
        if temp_oriented_file and os.path.exists(temp_oriented_file):
            try: os.remove(temp_oriented_file)
            except Exception: pass
            
        return temp_paths

    def close(self):
        """Cleans up Playwright resources."""
        print("[i] Closing browser connection...")
        try:
            if self.browser: self.browser.close()
            elif self.context: self.context.close()
        except Exception: pass
        try:
            if self.playwright: self.playwright.stop()
        except Exception: pass

# ------------------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------------------
def main():
    print("="*60)
    print("      GEMINI WEB AUTOMATION & IMAGE GENERATION BOT")
    print("="*60)
    
    # 1. Load Config
    config = load_config()
    
    # 2. Scan Input Images
    drive = DriveHandler(config)
    all_images = drive.get_input_images()
    print(f"\n[+] Scanned source folder. Found {len(all_images)} total image(s).")
    
    if not all_images:
        print("[-] No input images found. Please add images to input_images folder.")
        sys.exit(0)
        
    # Filter processed if skip_already_processed is enabled
    skip_processed = config.get("skip_already_processed", False)
    unprocessed_images = []
    
    if skip_processed:
        print("[i] Filtering out already processed images...")
        for img in all_images:
            if drive.check_if_already_processed(img['name']):
                print(f"  - [Skipped] '{img['name']}' has already been processed.")
            else:
                unprocessed_images.append(img)
    else:
        print("[i] Processing all images (regeneration/overwrite is enabled)...")
        unprocessed_images = all_images
        
    print(f"[i] Total images to process: {len(unprocessed_images)}")
    
    # Send start notification
    if config.get("notifications", {}).get("push_alerts", False):
        send_notification(
            config,
            f"🚀 **Gemini Product Photography Bot Started!**\n"
            f"• Total images in folder: {len(all_images)}\n"
            f"• Already processed (skipped): {len(all_images) - len(unprocessed_images)}\n"
            f"• Queue to process: {len(unprocessed_images)} image(s)."
        )
    
    # 3. Start Browser Automation
    bot = GeminiAutomation(config)
    try:
        bot.start()
        bot.verify_login()
    except Exception as e:
        print(f"\n[!!! ERROR !!!] Failed to start browser: {e}")
        bot.close()
        sys.exit(1)
        
    # 4. Iterate over images
    bot_state = BotState()
    bot_state.status = "Running"
    bot_state.total_images = len(unprocessed_images)
    bot_state.run_start_time = time.time()
    
    successful_count = 0
    failed_count = 0
    consecutive_failures = 0
    successful_since_new_chat = 0
    delay = config.get("delay_between_generations_sec", 10)
    
    # Check/Generate prompts.txt file in the script directory
    prompts_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts.txt')
    
    # If prompts.txt does not exist, create it with the default premium prompts
    if not os.path.exists(prompts_file_path):
        try:
            print("[i] Creating default 'prompts.txt' file with premium templates...")
            with open(prompts_file_path, 'w', encoding='utf-8') as f:
                # Separate prompts by '---' on a newline
                f.write("\n---\n".join(PREMIUM_PROMPTS))
            print("[+] 'prompts.txt' created successfully. You can edit this file to add or change prompts!")
        except Exception as e:
            print(f"Warning: Failed to create prompts.txt: {e}")
            
    # Load prompts from prompts.txt
    active_prompts_pool = PREMIUM_PROMPTS
    if os.path.exists(prompts_file_path):
        try:
            with open(prompts_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Split prompts by a line containing '---'
            raw_prompts = [p.strip() for p in re.split(r'\n\s*---\s*\n|\n\s*---\s*$', content) if p.strip()]
            if raw_prompts:
                active_prompts_pool = raw_prompts
                print(f"[+] Loaded {len(active_prompts_pool)} custom prompts from 'prompts.txt'.")
            else:
                print("[i] 'prompts.txt' is empty. Using default premium prompts.")
        except Exception as e:
            print(f"Warning: Failed to read prompts.txt ({e}). Using default premium prompts.")
            
    # Set up prompt shuffling pool if enabled
    use_shuffled = config.get("use_shuffled_prompts", True)
    if use_shuffled:
        prompts_pool = list(active_prompts_pool)
        random.shuffle(prompts_pool)
        print(f"[i] Shuffled prompt pool initialized with {len(prompts_pool)} templates.")
    else:
        print("[i] Shuffling is disabled. Using custom static prompt from config.")
        
    try:
        for idx, img in enumerate(unprocessed_images):
            # Update live state info
            bot_state.current_idx = idx + 1
            bot_state.current_image_name = img['name']
            check_telegram_status_requests(config, bot_state)
            
            print("\n" + "="*50)
            print(f" PROCESSING IMAGE {idx + 1} OF {len(unprocessed_images)}: '{img['name']}'")
            print("="*50)
            
            if use_shuffled:
                prompt_template = prompts_pool[idx % len(prompts_pool)]
                dress_desc = get_dress_description(img['name'])
                active_prompt = prompt_template.replace("[dress description]", dress_desc)
                print(f"[i] Selected Prompt Style #{ (idx % len(prompts_pool)) + 1 }")
                print(f"    Resolved Description: '{dress_desc}'")
            else:
                active_prompt = config.get("prompt")
            
            # Append strict dress features preservation and branding text instruction
            preservation_suffix = (
                "\nCRITICAL INSTRUCTION: You must preserve the dress from the uploaded image EXACTLY "
                "without altering, changing, or modifying any of its features. Do NOT alter the dress features even by 1%. "
                "You can enhance the realism, lighting, and background details, but the dress's embroideries, threadwork patterns, "
                "colors, shape, cut, design details, or fabric texture must remain completely unchanged and identical to the original photo."
                "\nBRANDING TEXT INSTRUCTION: At the bottom center of the image, below the dress, render the text 'Shiv Kripa' "
                "in a clean, elegant, luxury serif branding font. The size of the text 'Shiv Kripa' should be relatively small and delicate "
                "(approximately 8% to 10% of the image width, serving as a subtle and clean luxury signature branding). "
                "Directly beneath the text 'Shiv Kripa', add a thin horizontal separator line with a small floral/diamond motif accent in the middle. "
                "The color of the text 'Shiv Kripa' and the separator line must match the color theme of the dress (for example, if the dress has "
                "blue and pink details, use a matching shade of blue or pink for the text; if the dress is green/gold, use green/gold)."
            )
            active_prompt += preservation_suffix
                
            try:
                temp_paths = bot.run_generation(img['path'], active_prompt)
                
                if temp_paths:
                    saved_paths = drive.save_outputs(img['name'], temp_paths)
                    successful_count += 1
                    bot_state.successful_count = successful_count
                    consecutive_failures = 0  # Reset counter on successful generation
                    
                    # Send Discord/Telegram notification if push alerts are enabled
                    if config.get("notifications", {}).get("push_alerts", False):
                        first_img = saved_paths[0] if saved_paths else None
                        send_notification(
                            config,
                            f"✅ **Generation Successful!**\n"
                            f"• Image: `{img['name']}`\n"
                            f"• Generated: {len(temp_paths)} styled version(s)\n"
                            f"• Progress: {successful_count}/{len(unprocessed_images)} in this run",
                            image_path=first_img
                        )
                    successful_since_new_chat += 1
                    
                    # Auto-New Chat every 15 successful images to clear memory and save compute quota
                    if successful_since_new_chat >= 15:
                        print(f"[i] Successfully processed {successful_since_new_chat} images in this session.")
                        bot.start_new_chat()
                        successful_since_new_chat = 0
                else:
                    print(f"\n[!!! ERROR !!!] Failed: Gemini returned no images for '{img['name']}'")
                    failed_count += 1
                    bot_state.failed_count = failed_count
                    consecutive_failures += 1
                    
                # Clean up local temp files
                if temp_paths:
                    for p in temp_paths:
                        try:
                            if os.path.exists(p): os.remove(p)
                        except Exception: pass
            except Exception as e:
                err_str = str(e)
                print(f"\n[!!! ERROR !!!] Unexpected exception while processing '{img['name']}': {e}")
                failed_count += 1
                bot_state.failed_count = failed_count
                consecutive_failures += 1
                if "GEMINI_RATE_LIMIT_REACHED" in err_str:
                    msg = "🛑 **Rate Limit Abort!** Gemini is currently rate-limiting image generation. Stopping run."
                    print(f"\n[!!! RATE LIMIT REACHED !!!] {msg}")
                    send_notification(config, msg)
                    break
                    
            if consecutive_failures >= 3:
                msg = "🛑 **Abrupt Stop!** 3 images in a row failed to process. Check internet/session."
                print(f"\n[!!! CONSECUTIVE FAILURES ABRUPT STOP !!!] {msg}")
                send_notification(config, msg)
                break
                
            # Inter-image delay with live Telegram progress checking
            if idx < len(unprocessed_images) - 1:
                print(f"[i] Waiting {delay} seconds before starting the next image...")
                start_time = time.time()
                while time.time() - start_time < delay:
                    check_telegram_status_requests(config, bot_state)
                    time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n[i] Process interrupted by user. Safely shutting down...")
    finally:
        bot.close()
        bot_state.status = "Idle"
        
    # 5. Output Summary
    summary_msg = (
        f"🏁 **Batch Run Complete!**\n"
        f"• Total processed: {successful_count + failed_count}\n"
        f"• Successful: {successful_count}\n"
        f"• Failed: {failed_count}"
    )
    print("\n" + "="*60)
    print("                     RUN SUMMARY")
    print("="*60)
    print(f"Total processed:  {successful_count + failed_count}")
    print(f"Successful:       {successful_count}")
    print(f"Failed:           {failed_count}")
    print("="*60)
    print("Finished.")
    
    if config.get("notifications", {}).get("push_alerts", False):
        send_notification(config, summary_msg)

if __name__ == "__main__":
    # Force stdout/stderr flushing for real-time tracking in CMD
    sys.stdout.reconfigure(line_buffering=True)
    main()
