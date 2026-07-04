# Gemini Styled Product Photography Automation Bot

An automated, same-chat Playwright browser controller designed to transform raw flat lay dress photos into premium, studio-grade product shots with custom luxury watermark branding, utilizing Google Gemini's Imagen 3 engine.

---

## Key Features

* 🚀 **Same-Chat Session Continuity:** Iterates sequentially through the queue without refreshing the browser tab, maintaining prompt memory context and boosting execution speed.
* 📱 **Mobile Status Notifications (Discord / Telegram):** Sends real-time status alerts (Start, Success, Rate Limits, and Run Summary) directly to your phone. It even **attaches the generated photo** to the notification!
* 📝 **Dynamic Custom Prompts (`prompts.txt`):** Auto-generates a simple text file (`prompts.txt`) on startup. You can easily copy-paste, add, or change your prompts by separating them with a simple `---` line. The bot shuffles and rotates them automatically.
* 📐 **EXIF Auto-Orientation:** Automatically transposes sideways/landscape photos upright (straight) based on their EXIF tags.
* 🖼️ **HEIC/HEIF Support:** Automatically converts Apple HEIC files to standard high-quality JPEGs on the fly for absolute browser and upload compatibility.
* 🔐 **MD5 Content Hashing (Zero-Duplicate Sync):** Uses MD5 content fingerprinting to track processed files. Skips duplicate content even if files are renamed. If you overwrite/recopy a file to correct it, the bot deletes the old output and triggers a fresh generation.
* 🧠 **Memory & Compute Quota Optimizer:** Automatically starts a fresh chat session every **15 successful runs** to clear browser RAM and conserve your Gemini rolling compute limit.
* ⏳ **Slow Connection Failsafes:** Waits for active uploads to finish and automatically clears stuck/canceled upload thumbnails before beginning the next image.
* 🎨 **Watermark & Preservation prompts:** Locks in custom watermarks (like `Shiv Kripa`) centered at the bottom center with color-matching parameters, alongside strict instructions prohibiting altering dress embroidery, cuts, or patterns.

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
├── config.json                # Local paths, configurations, and browser options
├── prompts.txt                # Easy text file to copy-paste your prompts (separated by ---)
├── .gitignore                 # GitHub ignore config (safeguards private images/paths)
├── README.md                  # This file
└── project_recreation/
    └── RECREATION_GUIDE.md    # Developer guide for porting this to ChatGPT/Claude
```

---

## Setup & Installation

### 1. Clone & Install Dependencies
Ensure you have Python 3.9+ installed, then run:
```cmd
pip install playwright Pillow pillow-heif requests
playwright install chromium
```

### 2. Configure `config.json`
Create a `config.json` file in the root directory. Configure your source folders and Chrome profile path:
```json
{
  "source_folder": "C:\\path\\to\\your\\input_images",
  "destination_folder": "C:\\path\\to\\your\\output_images",
  "use_shuffled_prompts": true,
  "delay_between_generations_sec": 10,
  "skip_already_processed": true,
  "chrome_mode": "persistent",
  "chrome_profile_path": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Google\\Chrome\\User Data",
  "chrome_profile_name": "Default",
  "gemini_url": "https://gemini.google.com/app"
}
```

### 3. Log In to Google Gemini
Close all Google Chrome windows completely, then start the bot:
```cmd
python run_bot.py
```
* **First Run:** If the bot detects you are not logged in, it will pause, open Chrome, and wait for you to sign into your Google account. Once signed in and you see the Gemini chat screen, press **Enter** in the command prompt to begin automation.

---

## How to Recreate for ChatGPT or Claude
A comprehensive blueprint with web selectors, browser patterns, and a copy-paste prompt template is included in **[project_recreation/RECREATION_GUIDE.md](project_recreation/RECREATION_GUIDE.md)** if you wish to adapt this system to other LLM chat interfaces.
