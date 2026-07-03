import sys
import os
import json
import urllib.request
import urllib.error

def check_cdp(url):
    """Checks if Chrome CDP is accessible on the configured port."""
    try:
        # Check /json/version endpoint which is standard for CDP
        endpoint = f"{url}/json/version"
        print(f"Connecting to CDP endpoint: {endpoint}...")
        with urllib.request.urlopen(endpoint, timeout=3) as response:
            data = json.loads(response.read().decode())
            print("Successfully reached Chrome CDP!")
            print(f"  Browser: {data.get('Browser')}")
            print(f"  V8-Version: {data.get('V8-Version')}")
            return True
    except urllib.error.URLError as e:
        print(f"Failed to connect to CDP: {e}")
        return False
    except Exception as e:
        print(f"Error checking CDP endpoint: {e}")
        return False

def main():
    print("="*60)
    print("           GEMINI BOT - ENVIRONMENT VERIFICATION")
    print("="*60)
    
    # 1. Load config.json
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    if not os.path.exists(config_path):
        print("[-] config.json not found. Creating a default config...")
        # Create default config
        from run import load_config
        config = load_config()
    else:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
    print("[+] Loaded config.json")
    
    # 2. Check Directories
    source_folder = config.get("source_folder")
    dest_folder = config.get("destination_folder")
    
    print("\nChecking Directories:")
    if os.makedirs(source_folder, exist_ok=True) or True:
        print(f"  [+] Source directory: {source_folder} (Exists/Created)")
    if os.makedirs(dest_folder, exist_ok=True) or True:
        print(f"  [+] Destination directory: {dest_folder} (Exists/Created)")
        
    # Put a dummy file in source for testing if empty
    if len(os.listdir(source_folder)) == 0:
        print(f"  [i] Source folder is empty. Placing a sample placeholder file...")
        placeholder_path = os.path.join(source_folder, "test_placeholder.txt")
        with open(placeholder_path, "w") as f:
            f.write("This is a placeholder for testing files.")
            
    # 3. Check connection mode
    chrome_mode = config.get("chrome_mode", "cdp").lower()
    print(f"\nConfiguration Chrome Mode: {chrome_mode.upper()}")
    
    if chrome_mode == "cdp":
        cdp_url = config.get("chrome_cdp_url", "http://localhost:9222")
        print(f"Attempting to verify Chrome is running on debugging port (CDP)...")
        success = check_cdp(cdp_url)
        
        if success:
            print("\n[+] Verification SUCCESS: Chrome is running and ready for connection.")
        else:
            print("\n[-] Verification FAILED: Chrome is not running with Remote Debugging enabled.")
            print("\nTo fix this, please start Chrome with the remote debugging port enabled:")
            print("1. Close all active instances of Google Chrome completely.")
            print("2. Open Command Prompt or PowerShell and run:")
            print("   start chrome --remote-debugging-port=9222")
            print("3. Make sure you are logged into your Google Account / Gemini in that window.")
            print("4. Re-run this verification script.")
    else:
        print("Using Persistent Profile mode. Make sure all Chrome windows are closed when launching the bot.")
        
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
