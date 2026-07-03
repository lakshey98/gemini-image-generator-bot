# PROJECT RECREATION & ADAPTATION BLUEPRINT

This blueprint contains the complete technical details, code references, design patterns, and DOM selectors required to recreate this automation project or adapt it for other AI chat platforms (such as Claude.ai, ChatGPT, or custom GPT interfaces).

---

## 1. Project Architecture & Core Design Patterns

The project is built on six core design patterns to ensure high stability, no session resets, and bulletproof image handling:

### Pattern A: Same-Chat Iteration Loop
* **Why:** Opening new chat windows for every image causes slow generation speeds and model-context resets.
* **How:** The browser is launched once using a **persistent Chrome user profile**. The bot stays on the same page.
* **Failsafe Selector Targeting:** The bot always uses the `.last` selector modifier in Playwright. This ensures that even when the chat history grows, the bot always targets the active input field and the most recent response bubble.

### Pattern B: Natively Intercepted FileChooser Upload
* **Why:** Direct DOM file input injection can target hidden, stale input elements in the chat history, leading to false-positive uploads where the prompt is sent without the image.
* **How:** The bot clicks the "+" upload button to open the menu, then triggers the click on "Upload from computer" while listening to the browser's native `file_chooser` event. This guarantees that files are attached to the active input block.

### Pattern C: CORS-Bypassing Canvas Download
* **Why:** Google prevents downloading generated images directly via HTTP requests (such as `requests.get`) due to CORS policies and auth-token requirements.
* **How:** The bot runs JavaScript inside the browser context to draw the image onto an HTML5 `<canvas>` element and extracts the raw pixels as a base64 string, which is then saved locally.

### Pattern D: Auto-New Chat Session (Memory Clear & Token Saver)
* **Why:** Processing dozens of images in the same chat makes the browser DOM extremely heavy, slowing down Chrome. Furthermore, every prompt sends the entire chat history as context, wasting your hourly/daily Gemini compute quota.
* **How:** The bot tracks successful generations and automatically triggers a fresh chat redirect (`start_new_chat()`) every **15 successful images** to clear RAM and save compute limits.

### Pattern E: Generic Consecutive Failures Auto-Abort
* **Why:** If the internet drops or a session expires, the bot shouldn't cycle through the remaining images in the folder and mark them all as failed.
* **How:** The loop maintains a `consecutive_failures` counter. If **3 images in a row fail** to generate any outputs, the bot aborts the execution cleanly, leaving unprocessed images in the queue for a future resume.

### Pattern F: Rate-Limit Text Scans
* **Why:** If Gemini is overloaded, it returns text responses (like *"I can't generate images right now"*) instead of image files, which causes the bot to wait unnecessarily.
* **How:** If no images are found, the bot scans the latest response bubble for common rate-limit phrases and immediately aborts the run if a block is detected.

---

## 2. Folder Structure

```text
gemini-image-generator-bot/
├── run_bot.py           # Main automation, file handler, and browser controller
├── config.json          # System paths, configurations, and prompt templates
└── requirements.txt     # Python dependencies
```

---

## 3. Configuration Template (`config.json`)

Save this as `config.json` in the root directory:

```json
{
  "source_folder": "C:\\path\\to\\input_images",
  "destination_folder": "C:\\path\\to\\output_images",
  "use_shuffled_prompts": true,
  "delay_between_generations_sec": 10,
  "skip_already_processed": true,
  "chrome_mode": "persistent",
  "chrome_cdp_url": "http://127.0.0.1:9222",
  "chrome_profile_path": "C:\\Users\\YOUR_USER\\AppData\\Local\\Google\\Chrome\\User Data",
  "chrome_profile_name": "Default",
  "gemini_url": "https://gemini.google.com/app",
  "prompts_pool": [
    "Top-down flat lay, expert product photography of a [dress description] on a rich champagne gold satin silk background. Render the text 'Shiv Kripa' at the bottom center. --ar 1:1"
  ]
}
```

---

## 4. Complete System Code (`run_bot.py`)

Here is the complete source code for the automated controller, including HEIC conversion, EXIF auto-rotation, and upload safety loops:

```python
import os
import sys
import re
import json
import time
import shutil
import random
import tempfile
import base64
import requests
from playwright.sync_api import sync_playwright

# Core Supported Formats
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.heic', '.heif')

DEFAULT_CONFIG = {
    "source_folder": "./input_images",
    "destination_folder": "./output_images",
    "use_shuffled_prompts": True,
    "delay_between_generations_sec": 10,
    "skip_already_processed": True,
    "chrome_mode": "persistent",
    "chrome_cdp_url": "http://127.0.0.1:9222",
    "chrome_profile_path": "",
    "chrome_profile_name": "Default",
    "gemini_url": "https://gemini.google.com/app"
}

def get_file_hash(file_path):
    """Calculates MD5 hash of a file to check for content modifications, bypassing time discrepancy bugs."""
    import hashlib
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

class DriveHandler:
    def __init__(self, config):
        self.config = config
        self.source_folder = config["source_folder"]
        self.destination_folder = config["destination_folder"]
        self.metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed_metadata.json')
        self.metadata = self.load_metadata()
        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(self.destination_folder, exist_ok=True)

    def load_metadata(self):
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception: pass
        return {}

    def save_metadata(self):
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception: pass

    def get_input_images(self):
        file_list = []
        for f in os.listdir(self.source_folder):
            if f.lower().endswith(IMAGE_EXTENSIONS):
                if "_gen_" in f:
                    continue
                file_path = os.path.join(self.source_folder, f)
                file_list.append((f, file_path, os.path.getmtime(file_path)))
        file_list.sort(key=lambda x: x[2])  # Chronological sorting
        return [{'name': f, 'path': path} for f, path, _ in file_list]

    def check_if_already_processed(self, input_filename):
        base_name, _ = os.path.splitext(input_filename)
        input_path = os.path.join(self.source_folder, input_filename)
        if not os.path.exists(input_path) or not os.path.exists(self.destination_folder):
            return False
            
        current_hash = get_file_hash(input_path)
        if not current_hash:
            return False
            
        # 1. Duplicate Content Check
        for name, h in self.metadata.items():
            if h == current_hash and name != input_filename:
                other_base, _ = os.path.splitext(name)
                other_output_exists = False
                for f in os.listdir(self.destination_folder):
                    if f.startswith(other_base) and f.lower().endswith(IMAGE_EXTENSIONS) and "gen" in f:
                        other_output_exists = True
                        break
                if other_output_exists:
                    print(f"  - [Skipped] '{input_filename}' contains identical image content to already processed '{name}'. Skipping duplicate.")
                    return True
            
        # 2. Get matching outputs
        has_output = False
        for f in os.listdir(self.destination_folder):
            if f.startswith(base_name) and f.lower().endswith(IMAGE_EXTENSIONS) and "gen" in f:
                has_output = True
                break
                
        if has_output:
            stored_hash = self.metadata.get(input_filename)
            if not stored_hash:
                self.metadata[input_filename] = current_hash
                self.save_metadata()
                return True
                
            if current_hash != stored_hash:
                print(f"[i] Input file '{input_filename}' content has been updated/recopied. Triggering re-processing...")
                for f in os.listdir(self.destination_folder):
                    if f.startswith(base_name) and f.lower().endswith(IMAGE_EXTENSIONS) and "gen" in f:
                        try: os.remove(os.path.join(self.destination_folder, f))
                        except Exception: pass
                return False
            return True
        return False

    def save_outputs(self, input_filename, temp_image_paths):
        base_name, _ = os.path.splitext(input_filename)
        for i, temp_path in enumerate(temp_image_paths):
            ext = os.path.splitext(temp_path)[1]
            dest_path = os.path.join(self.destination_folder, f"{base_name}_gen_{i+1}{ext}")
            shutil.copy(temp_path, dest_path)
            try:
                orig_path = os.path.join(self.source_folder, input_filename)
                if os.path.exists(orig_path):
                    os.utime(dest_path, (os.path.getatime(orig_path), os.path.getmtime(orig_path)))
            except Exception: pass
            
        try:
            orig_path = os.path.join(self.source_folder, input_filename)
            current_hash = get_file_hash(orig_path)
            if current_hash:
                self.metadata[input_filename] = current_hash
                self.save_metadata()
        except Exception: pass

class GeminiAutomation:
    def __init__(self, config):
        self.config = config
        self.chrome_mode = config.get("chrome_mode", "persistent").lower()
        self.chrome_cdp_url = config.get("chrome_cdp_url")
        self.chrome_profile_path = config.get("chrome_profile_path")
        self.chrome_profile_name = config.get("chrome_profile_name", "Default")
        self.gemini_url = config.get("gemini_url")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        if self.chrome_mode == "cdp":
            self.browser = self.playwright.chromium.connect_over_cdp(self.chrome_cdp_url)
            self.context = self.browser.contexts[0]
            self.page = self.context.pages[0]
        else:
            profile_dir = os.path.join(self.chrome_profile_path, self.chrome_profile_name)
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                channel="chrome",
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            self.page = self.context.pages[0]
        self.page.set_viewport_size({"width": 1280, "height": 800})

    def safe_goto(self, url, retries=3):
        for attempt in range(retries):
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self.page.wait_for_timeout(2000)
                return True
            except Exception:
                if attempt < retries - 1: self.page.wait_for_timeout(4000)
        raise RuntimeError("Navigation failed.")

    def verify_login(self):
        self.safe_goto(self.gemini_url)
        textbox = self.page.locator('.ql-editor[contenteditable="true"], [role="textbox"], textarea').first
        if textbox.count() == 0:
            input("Please log in on Chrome and press Enter here...")
            self.safe_goto(self.gemini_url)

    def start_new_chat(self):
        print("[i] Cleaning up memory and starting a fresh chat session...")
        self.safe_goto(self.gemini_url)
        textbox = self.page.locator('.ql-editor[contenteditable="true"], [role="textbox"], textarea').last
        textbox.wait_for(state="visible", timeout=30000)

    def run_generation(self, image_path, prompt):
        # 1. Busy check: wait until previous generation completes
        stop_btn_selectors = ['button[aria-label*="Stop" i]', '[aria-label*="Stop generating" i]']
        is_generating = True
        while is_generating:
            found_stop = False
            for sel in stop_btn_selectors:
                try:
                    btn = self.page.locator(sel).last
                    if btn.count() > 0 and btn.is_visible():
                        found_stop = True
                        break
                except Exception: pass
            if found_stop:
                self.page.wait_for_timeout(5000)
            else:
                is_generating = False

        # Focus input
        textbox = self.page.locator('.ql-editor[contenteditable="true"], [role="textbox"], textarea').last
        textbox.wait_for(state="visible", timeout=30000)
        textbox.focus()

        # 2. Slow Connection Protection: Wait for active uploads to finish
        loading_selectors = ['mat-progress-bar', '.progress-bar', '.loading-spinner']
        for sel in loading_selectors:
            try:
                loader = self.page.locator(sel).last
                if loader.count() > 0 and loader.is_visible():
                    loader.wait_for(state="hidden", timeout=30000)
            except Exception: pass

        # 3. Clean stuck attachments
        clear_btn_selectors = ['button[aria-label*="Remove" i]', '.remove-button', 'button:has(svg[path*="close" i])']
        input_container = self.page.locator('.chat-input-container, .textarea-wrapper, form').last
        if input_container.count() > 0:
            for sel in clear_btn_selectors:
                try:
                    btn = input_container.locator(sel).last
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=3000)
                        self.page.wait_for_timeout(1000)
                except Exception: pass

        # 4. Auto-orient/straighten and convert HEIC
        upload_path = image_path
        temp_oriented_file = None
        try:
            from PIL import Image, ImageOps
            import pillow_heif
            pillow_heif.register_heif_opener()
            img_obj = Image.open(image_path)
            oriented_img = ImageOps.exif_transpose(img_obj)
            is_heic = image_path.lower().endswith(('.heic', '.heif'))
            if is_heic or (img_obj.size != oriented_img.size):
                fd, temp_oriented_file = tempfile.mkstemp(suffix=".jpg")
                os.close(fd)
                if oriented_img.mode in ("RGBA", "P"):
                    oriented_img = oriented_img.convert("RGB")
                oriented_img.save(temp_oriented_file, "JPEG", quality=95)
                upload_path = temp_oriented_file
        except Exception: pass

        # 5. Upload File (FileChooser priority)
        uploaded = False
        if upload_path and os.path.exists(upload_path):
            try:
                upload_btn = self.page.locator('button[aria-label*="Add files" i], [aria-label*="Upload" i]').last
                upload_btn.click(timeout=5000, no_wait_after=True)
                self.page.wait_for_timeout(2000)
                
                menu_item = self.page.locator('span:has-text("Upload files"), [aria-label*="computer" i]').last
                with self.page.expect_file_chooser(timeout=5000) as fc_info:
                    menu_item.click(timeout=5000, no_wait_after=True)
                file_chooser = fc_info.value
                file_chooser.set_files(upload_path)
                self.page.wait_for_timeout(3000)
                uploaded = True
            except Exception:
                # Direct injection fallback
                try:
                    file_input = self.page.locator('input[type="file"]').last
                    file_input.set_input_files(upload_path, timeout=5000)
                    self.page.wait_for_timeout(3000)
                    uploaded = True
                except Exception: pass

            if not uploaded:
                raise RuntimeError("Image upload failed.")

        # 6. Submit Prompt and Failsafe Send Verification
        textbox.fill(prompt)
        self.page.wait_for_timeout(1000)
        send_btn = self.page.locator('button[aria-label*="Send" i], button:has-text("Send")').last

        # Wait for file attachment load to complete
        for _ in range(20):
            if send_btn.is_enabled() and not send_btn.get_attribute("disabled"):
                break
            self.page.wait_for_timeout(1000)

        # Submit & Retry loop
        sent = False
        for send_attempt in range(3):
            try:
                if send_btn.is_enabled() and not send_btn.get_attribute("disabled"):
                    send_btn.click(timeout=5000, no_wait_after=True)
                else:
                    textbox.press("Enter")
                
                self.page.wait_for_timeout(2000)
                val = textbox.input_value() if hasattr(textbox, 'input_value') else ""
                if not val.strip():
                    sent = True
                    break
            except Exception: pass
            
            # Fallback enter press
            try:
                textbox.focus()
                textbox.press("Enter")
                self.page.wait_for_timeout(2000)
            except Exception: pass

        # 7. Wait for Completion
        good_response_btn = self.page.locator('button[aria-label*="Good response" i], .response-actions').last
        good_response_btn.wait_for(state="visible", timeout=180000)
        self.page.wait_for_timeout(5000)

        # 8. Canvas Extraction (CORS Bypass & Input Image Exclusion Filter)
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
                        if (img.closest('user-query, .query-content, .user-message, .input-image, .attachment-preview, g-image-attachment, .chat-input-container')) {
                            continue;
                        }
                        if ((img.naturalWidth || img.width) > 100) validImgs.push(img);
                    }
                    if (validImgs.length > 0) {
                        return validImgs.map(img => {
                            try {
                                const canvas = document.createElement('canvas');
                                canvas.width = img.naturalWidth || img.width;
                                canvas.height = img.naturalHeight || img.height;
                                canvas.getContext('2d').drawImage(img, 0, 0);
                                return { src: img.src, base64: canvas.toDataURL('image/png').split(',')[1] };
                            } catch (e) { return { src: img.src, base64: null }; }
                        });
                    }
                    container = container.parentElement;
                }
                return [];
            }
        """)

        # Clean temp orientation file
        if temp_oriented_file and os.path.exists(temp_oriented_file):
            try: os.remove(temp_oriented_file)
            except Exception: pass

        # 9. Rate Limit Text Verification
        if not image_data:
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
            except Exception: pass
            
            rate_limit_keywords = ["create more images than usual", "can't do that for you right now", "ask me again later", "reached your limit", "generation limit"]
            for keyword in rate_limit_keywords:
                if keyword.lower() in latest_response_text.lower():
                    raise RuntimeError("GEMINI_RATE_LIMIT_REACHED")
            return []

        # Download extracted canvas images
        temp_paths = []
        for i, item in enumerate(image_data):
            if item.get('base64'):
                fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                with open(temp_path, 'wb') as f:
                    f.write(base64.b64decode(item['base64']))
                temp_paths.append(temp_path)
        return temp_paths

    def close(self):
        if self.browser: self.browser.close()
        elif self.context: self.context.close()
        if self.playwright: self.playwright.stop()
```

---

## 5. Cheat Sheet of Target Web Selectors

| Action / State | Gemini Selector | Claude.ai Selector | ChatGPT Selector |
| :--- | :--- | :--- | :--- |
| **Active Textbox** | `.ql-editor[contenteditable="true"]` | `[contenteditable="true"]` | `#prompt-textarea` |
| **Upload Button** | `button[aria-label*="Add files" i]` | `button[aria-label*="Upload" i]` | `button[aria-label*="Attach" i]` |
| **Computer Upload** | `span:has-text("Upload files")` | *(Direct Native Dialog)* | *(Direct Native Dialog)* |
| **Send Button** | `button[aria-label*="Send" i]` | `button[aria-label*="Send" i]` | `button[data-testid="send-button"]` |
| **Busy/Stop Button** | `button[aria-label*="Stop" i]` | `button[aria-label*="Stop" i]` | `button[aria-label*="Stop" i]` |
| **Success Indicator**| `button[aria-label*="Good response" i]` | `button[aria-label*="Helpful" i]` | `button[aria-label*="Copy" i]` |

---

## 6. Prompt to Hand Over to Another AI Assistant (Claude, GPT-4, etc.)

When starting a project for a different GPT or interface, copy and paste this prompt:

> **PROMPT FOR NEW GPT:**
> "I want to create an image generation automation system for [INSERT MODEL NAME HERE, e.g., Claude/ChatGPT]. Read the attached `RECREATION_GUIDE.md` which details the same-chat Playwright pattern, the FileChooser upload flow, and the CORS-bypassing canvas download logic. Adapt this architecture to generate script modifications targeting the DOM selectors listed in Section 5, ensuring zero-session resets and sequential execution."

---

## 7. Edge Cases, Errors, & Failsafe Solutions

When recreating or adapting this automation, build in these specific protections to solve common web-scraping bugs:

### Case 1: Windows File Copy Date Retention (Re-processing Bypass)
* **Problem:** When a user overwrites an input file to correct a bad image, Windows may preserve the original modification time (`mtime`). Because the file time appears older than the generated output, the bot incorrectly skips the correction.
* **Solution:** Do not rely on file dates. Calculate the **MD5 content hash** of the input image and store it in a database file (`processed_metadata.json`). Check if the current file's hash matches the stored hash. If they differ, trigger regeneration and delete outdated outputs.

### Case 2: Slow Internet Connection (Stuck Attachments / Prompt-Only Sent)
* **Problem:** In slow network conditions, the bot clicks the Send button before the image is fully attached, resulting in a text-only prompt being submitted.
* **Solution:** Check the Send button state. If the button is disabled, pause in a loop for up to 20 seconds. Additionally, check if the input textarea is cleared after clicking; if it is not, trigger a fallback `Enter` key press and retry up to 3 times.

### Case 3: Stale Attachment Previews in Input Wrapper
* **Problem:** If a previous upload fails or times out, the image remains stuck in the chat input area. The bot then uploads a second image, sending both photos together.
* **Solution:** Before initiating any upload, scan the active bottom chat input container for any visible close/delete buttons (e.g. `button[aria-label*="Remove" i]`). If found, click them to clear the slate.

### Case 4: Stale Input Nodes in Chat History (Double Uploads)
* **Problem:** As chat history grows, multiple hidden `<input type="file">` elements accumulate. Direct injection (`locator('input[type="file"]').set_input_files(...)`) may target a hidden input from an old message, causing upload failures.
* **Solution:** Always click the upload button first to mount a new active input, then capture and use Playwright’s native `FileChooser` event.

### Case 5: Out of Memory (Chrome Tab Crashes)
* **Problem:** Running a single-chat session for dozens of images accumulates a massive DOM and makes Chrome sluggish.
* **Solution:** Maintain an in-memory counter of successful generations. Every **15 images**, force the browser to navigate back to the home URL (`https://gemini.google.com/app`) to initialize a fresh, empty conversation thread and clean up browser memory.

### Case 6: Rate Limiting (Overload Errors)
* **Problem:** Gemini blocks image generation after dozens of inputs. Continuing to process causes consecutive failed logs.
* **Solution:** Scan the latest response bubble for common rate-limit phrases (e.g., *"create more images than usual"*, *"ask me again later"*). If any match, raise a custom exception and abort the script immediately. Implement a backup abort if **3 consecutive images** fail to return output files for any reason.

### Case 7: Accidental Copy-Back of Outputs
* **Problem:** The user accidentally copies generated output files (e.g., `IMG_0252_gen_1.png`) back into the `input_images` folder, causing duplicate loops.
* **Solution:** Filter the folder scanner list. Skip any file containing the `_gen_` substring in its name during directory scanning.

