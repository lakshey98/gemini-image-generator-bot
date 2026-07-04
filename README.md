# Gemini Styled Product Photography Automation Bot

An automated, same-chat Playwright browser controller designed to transform raw flat lay dress photos into premium, studio-grade product shots with custom luxury watermark branding, utilizing Google Gemini's Imagen 3 engine.

---

## Key Features

* 🚀 **Same-Chat Session Continuity:** Iterates sequentially through the queue without refreshing the browser tab, maintaining prompt memory context and boosting execution speed.
* 📱 **On-Demand Progress Checks (Telegram):** Type `/status` in your Telegram bot chat at any time, and the bot will reply with a live progress report including remaining images and a dynamically calculated **Estimated Time Left (ETA)**.
* 🔇 **Zero Spam & Silent Runs:** Routine notifications (Startup, Success, Finished) are disabled by default (`"push_alerts": false`). The bot stays quiet and only speaks when you ask it for progress, and **never** sends image files to Telegram.
* 📝 **Dynamic Custom Prompts (`prompts.txt`):** Auto-generates a simple text file (`prompts.txt`) on startup. You can easily copy-paste, add, or change your prompts by separating them with a simple `---` line. The bot shuffles and rotates them automatically.
* 📐 **EXIF Auto-Orientation:** Automatically transposes sideways/landscape photos upright (straight) based on their EXIF tags.
* 🖼️ **HEIC/HEIF Support:** Automatically converts Apple HEIC files to standard high-quality JPEGs on the fly for absolute browser and upload compatibility.
* 🔐 **MD5 Content Hashing (Zero-Duplicate Sync):** Uses MD5 content fingerprinting to track processed files. Skips duplicate content even if files are renamed. If you overwrite/recopy a file to correct it, the bot deletes the old output and triggers a fresh generation.
* 🧠 **Memory & Compute Quota Optimizer:** Automatically starts a fresh chat session every **15 successful runs** to clear browser RAM and conserve your Gemini rolling compute limit.
* ⏳ **Slow Connection Failsafes:** Waits for active uploads to finish and automatically clears stuck/canceled upload thumbnails before beginning the next image.
* 🎨 **Watermark & Preservation prompts:** Locks in custom watermarks (like `Shiv Kripa`) centered at the bottom center with color-matching parameters, alongside strict instructions prohibiting altering dress embroidery, cuts, or patterns.

---

## Setup Guide for Another PC / Laptop

Follow this guide to set up and run this bot on any new computer (Windows or macOS) out-of-the-box:

### 1. Prerequisites (Any Machine)
1. **Python 3.9+:** Download and install Python from [python.org](https://www.python.org/downloads/). *(Make sure to check "Add Python to PATH" during installation).*
2. **Google Chrome:** Ensure Google Chrome is installed on the computer.

### 2. Install Project Dependencies
Open your Command Prompt (Windows) or Terminal (Mac) inside the project folder and run:
```cmd
pip install playwright Pillow pillow-heif requests
playwright install chromium
```

### 3. Configure `config.json` (PC-Specific Settings)
Copy `config.json` to the new computer and customize these paths:

```json
{
  "source_folder": "./input_images",
  "destination_folder": "./output_images",
  "use_shuffled_prompts": true,
  "delay_between_generations_sec": 10,
  "skip_already_processed": true,
  "chrome_mode": "persistent",
  "chrome_profile_path": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Google\\Chrome\\User Data",
  "chrome_profile_name": "Default",
  "gemini_url": "https://gemini.google.com/app",
  "notifications": {
    "enabled": false,
    "platform": "telegram",
    "push_alerts": false,
    "webhook_url": "",
    "telegram_token": "",
    "telegram_chat_id": ""
  }
}
```

#### How to configure paths on the new PC:
* **Image Folders:** You can use relative paths like `"./input_images"` and `"./output_images"`. The bot will automatically create these folders inside the project directory, making it fully portable!
* **Finding your `chrome_profile_path`:**
  * **Windows:** Replace `YOUR_USERNAME` with the new computer's Windows username:
    `C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Google\\Chrome\\User Data`
  * **macOS:** Use the Mac default path (replace `YOUR_USERNAME` with your Mac username):
    `/Users/YOUR_USERNAME/Library/Application Support/Google/Chrome`
* **Finding your `chrome_profile_name`:**
  * If you use your primary Chrome profile, leave it as `"Default"`.
  * If you created a separate Chrome Profile (e.g. Profile 2), change it to `"Profile 2"`, `"Profile 3"`, etc.

### 4. Log In and Run
1. Close all open Google Chrome windows on the computer.
2. In the terminal, run the bot:
   ```cmd
   python run_bot.py
   ```
3. **First-Time Login:** The bot will automatically launch a new Chrome window. Because it's a new PC, you won't be signed in. Log in to your Google Account on the opened Gemini webpage.
4. Once you are signed in and see the chat page, go to the command prompt console and press **Enter** to start the automatic loop!

---

## Machine & Network Resilience Guidelines

The bot is designed to run reliably on any desktop machine and adapt dynamically to fast, slow, or unstable internet networks:

### 1. Machine & OS Compatibility (Any PC)
* **Cross-Platform:** Runs seamlessly on **Windows, macOS (including Apple Silicon M1/M2/M3), and Linux**.
* **Smart Paths:** Path references automatically adapt to use Windows backslashes (`\`) or Unix/Mac forward slashes (`/`).
* **Independent Browser:** Playwright manages its own Chromium binaries, isolated from changes to your system's default Chrome application.

### 2. Network & Internet Resilience
* **Upload Progress Tracker:** The bot pauses submission until all background progress indicators (`mat-progress-bar`, `.progress-bar`) disappear.
* **Failsafe Send Verification:** Confirms that the input box successfully clears after sending. If a packet drops or a click misses, it retries with physical `Enter` keys up to 3 times.
* **Resilient Navigation (`safe_goto`):** Includes a built-in navigation loop that retries up to 3 times with exponential delays if a page fails to load.
* **3-Failure Safety Abort:** If your internet disconnects completely, the bot shuts down cleanly after 3 consecutive failures to preserve your unprocessed image queue for later resumption.

---

## Real-Time Mobile Notifications Setup

To receive updates on your phone while the bot runs in the background, open your `config.json` and customize the `notifications` block:

### A. Discord Webhooks (Easiest & Recommended)
1. Open Discord, go to your server settings, click **Integrations** -> **Webhooks**, and click **Create Webhook**.
2. Copy the Webhook URL.
3. Configure `config.json` like this:
   ```json
   "notifications": {
     "enabled": true,
     "platform": "discord",
     "webhook_url": "https://discord.com/api/webhooks/...",
     "telegram_token": "",
     "telegram_chat_id": ""
   }
   ```

### B. Telegram Bots
1. Message **@BotFather** on Telegram and create a new bot to receive your API token.
2. Message **@userinfobot** to find your Telegram account's numeric Chat ID.
3. Configure `config.json` like this:
   ```json
   "notifications": {
     "enabled": true,
     "platform": "telegram",
     "webhook_url": "",
     "telegram_token": "123456789:ABCdefGhI...",
     "telegram_chat_id": "987654321"
   }
   ```

---

## Folder Structure

```text
gemini-image-generator-bot/
├── run_bot.py                 # Core controller, Playwright loop, and file engine
├── telegram_status.py         # Notifications module, ETA calculator, status listener
├── config.json                # Local paths, configurations, and browser options
├── prompts.txt                # Easy text file to copy-paste your prompts (separated by ---)
├── .gitignore                 # GitHub ignore config (safeguards private images/paths)
├── README.md                  # This file
└── project_recreation/
    └── RECREATION_GUIDE.md    # Developer guide for porting this to ChatGPT/Claude
```

---

## How to Recreate for ChatGPT or Claude
A comprehensive blueprint with web selectors, browser patterns, and a copy-paste prompt template is included in **[project_recreation/RECREATION_GUIDE.md](project_recreation/RECREATION_GUIDE.md)** if you wish to adapt this system to other LLM chat interfaces.
