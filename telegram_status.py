import os
import time
import json
import requests
import re

class BotState:
    def __init__(self):
        self.status = "Idle" # "Running", "Finished", "Idle"
        self.total_images = 0
        self.current_idx = 0
        self.current_image_name = "None"
        self.successful_count = 0
        self.failed_count = 0
        self.run_start_time = 0.0

def send_notification(config, message, image_path=None):
    """Sends a notification to Discord or Telegram if configured."""
    notif_cfg = config.get("notifications", {})
    if not notif_cfg.get("enabled", False):
        return
        
    platform = notif_cfg.get("platform", "discord").lower()
    
    if platform == "discord":
        url = notif_cfg.get("webhook_url")
        if not url or "YOUR_DISCORD_WEBHOOK_URL" in url:
            return
        try:
            if image_path and os.path.exists(image_path):
                # Send with image attachment
                with open(image_path, 'rb') as f:
                    files = {
                        'file': (os.path.basename(image_path), f, 'image/png')
                    }
                    data = {
                        'payload_json': json.dumps({'content': message})
                    }
                    response = requests.post(url, data=data, files=files, timeout=15)
            else:
                # Send text only
                payload = {'content': message}
                response = requests.post(url, json=payload, timeout=15)
        except Exception as e:
            print(f"[i] Notification Warning: Failed to send Discord notification: {e}")
            
    elif platform == "telegram":
        token = notif_cfg.get("telegram_token")
        chat_id = notif_cfg.get("telegram_chat_id")
        if not token or not chat_id or "YOUR_TELEGRAM" in token:
            return
        try:
            # Send text only (no image attachments as requested by user)
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=payload, timeout=15)
        except Exception as e:
            print(f"[i] Notification Warning: Failed to send Telegram notification: {e}")

def check_telegram_status_requests(config, bot_state):
    """Checks for status/progress commands sent to the Telegram bot and replies in real-time."""
    notif_cfg = config.get("notifications", {})
    if not notif_cfg.get("enabled", False) or notif_cfg.get("platform", "discord").lower() != "telegram":
        return
        
    token = notif_cfg.get("telegram_token")
    if not token or "YOUR_TELEGRAM" in token:
        return
        
    # Store last handled update_id to avoid repeating replies
    last_update_id_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.last_tg_update_id')
    last_update_id = 0
    if os.path.exists(last_update_id_file):
        try:
            with open(last_update_id_file, 'r') as f:
                last_update_id = int(f.read().strip())
        except Exception: pass
        
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 0}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            return
            
        updates = response.json().get("result", [])
        for update in updates:
            update_id = update.get("update_id")
            if update_id > last_update_id:
                last_update_id = update_id
                with open(last_update_id_file, 'w') as f:
                    f.write(str(last_update_id))
                    
            message = update.get("message", {})
            text = message.get("text", "").strip().lower()
            chat_id = message.get("chat", {}).get("id")
            
            if text in ["/status", "/progress", "status", "progress"]:
                if bot_state.status == "Running":
                    processed = bot_state.successful_count + bot_state.failed_count
                    remaining = bot_state.total_images - processed
                    
                    # Estimate remaining time
                    eta_str = "Calculating..."
                    if processed > 0:
                        elapsed = time.time() - bot_state.run_start_time
                        avg_time = elapsed / processed
                        eta_seconds = avg_time * remaining
                        
                        # Convert to mins/secs
                        mins = int(eta_seconds // 60)
                        secs = int(eta_seconds % 60)
                        if mins > 0:
                            eta_str = f"~{mins}m {secs}s"
                        else:
                            eta_str = f"~{secs}s"
                    else:
                        # Default estimate of 60s per image
                        eta_seconds = 60 * remaining
                        mins = int(eta_seconds // 60)
                        secs = int(eta_seconds % 60)
                        eta_str = f"~{mins}m {secs}s (est.)"
                        
                    report = (
                        f"📊 **Gemini Bot Progress Report**\n"
                        f"-----------------------------------------\n"
                        f"⚡ **Status:** RUNNING\n"
                        f"📸 **Current Image:** `{bot_state.current_image_name}`\n"
                        f"🔄 **Current Index:** {bot_state.current_idx} of {bot_state.total_images}\n"
                        f"✅ **Successful:** {bot_state.successful_count}\n"
                        f"❌ **Failed:** {bot_state.failed_count}\n"
                        f"⏳ **Remaining:** {remaining} image(s)\n"
                        f"🕒 **Estimated Time Left:** {eta_str}"
                    )
                else:
                    report = (
                        f"💤 **Gemini Bot Status: IDLE**\n\n"
                        f"• Last Run Summary:\n"
                        f"  - Successful: {bot_state.successful_count}\n"
                        f"  - Failed: {bot_state.failed_count}\n"
                        f"• No active batch currently running."
                    )
                
                reply_url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {'chat_id': chat_id, 'text': report, 'parse_mode': 'Markdown'}
                requests.post(reply_url, json=payload, timeout=5)
                
    except Exception as e:
        pass
