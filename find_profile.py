import os
import json

def main():
    user_data_path = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data"
    local_state_path = os.path.join(user_data_path, "Local State")
    target_profile_name = "LAKSHEY 35"
    
    print(f"Checking Local State at '{local_state_path}'...")
    
    if not os.path.exists(local_state_path):
        print(f"Error: Chrome Local State file '{local_state_path}' does not exist.")
        return
        
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            info_cache = data.get("profile", {}).get("info_cache", {})
            
            found = False
            for folder, info in info_cache.items():
                name = info.get("name")
                shortcut_name = info.get("shortcut_name")
                user_name = info.get("user_name")
                
                # Check match against name or shortcut name
                if target_profile_name.lower() in [str(name).lower(), str(shortcut_name).lower(), str(user_name).lower()]:
                    print(f"\n[+] SUCCESS! Found profile:")
                    print(f"  Folder: {folder}")
                    print(f"  Profile Name: {name}")
                    print(f"  Shortcut Name: {shortcut_name}")
                    print(f"  User Email/Name: {user_name}")
                    found = True
                    break
            
            if not found:
                print(f"\n[-] Profile '{target_profile_name}' not found in Local State.")
                print("All profiles in Local State:")
                for folder, info in info_cache.items():
                    print(f"  - Folder: '{folder}'")
                    print(f"    Name: '{info.get('name')}'")
                    print(f"    Shortcut: '{info.get('shortcut_name')}'")
                    print(f"    Email: '{info.get('user_name')}'")
                    
    except Exception as e:
        print(f"Error parsing Local State: {e}")

if __name__ == "__main__":
    main()
