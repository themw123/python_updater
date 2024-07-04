import json
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
import requests
import zipfile
#Do not remove this import, it is needed for cx_freeze to work correctly
import encodings.cp437 

class Updater:
    
    def __init__(self, config, type):
        self.config = config
        self.type = type
        self.sha = None
        self.extension = os.path.splitext(sys.argv[0])[1]
        self.os_type = platform.system()
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        
    def run(self):
        if self.os_type not in ['Windows', 'Linux']:
            print("\n- unsupported os. Only Windows and Linux are supported. Leaving updater...")
            return
        if self.extension == ".py":
            print("\n- you are in dev mode. Leaving updater...")
            return
        if len(sys.argv) > 1:
            try:
                print("\n- deleting old version...")
                print("\n- your old config.json was overwritten by the new one. Adjust the new one if necessary.")
                old_dir = sys.argv[1]
                shutil.rmtree(old_dir)
            except Exception as e:
                print("\n- Could not delete folder of old version, because the terminal of the previous version is still open. Delete it by yourself. Path:", old_dir)
                return
            return
        else:
            print("\n- checking for updates...")
         
         
            
        update_url = self.set_sha_and_check_for_update()
        if self.type == "backend":
            if self.os_type == 'Windows':
                import msvcrt
                def input_ready():
                    return msvcrt.kbhit()
            '''
            #no need for that. Currently backend is only supportet for windows
            else:
                import select
                def input_ready():
                    return select.select([sys.stdin], [], [], 0.0)[0]
            '''
            if update_url:
                print("\n- do you want to install the update? (yes/no): ")
                start_time = time.time()
                user_input = ""
                while time.time() - start_time < 5:
                    if input_ready():
                        user_input = input().lower()
                        break
                    time.sleep(0.1)
                
                if user_input == 'yes':
                    self.download_update(update_url)
        else:
            if update_url:
                user_input = input("\n- do you want to install the update? (yes/no): ")
                if user_input.lower() == 'yes':
                    self.download_update(update_url)
                
    def set_sha_and_check_for_update(self):
        api_url = "https://api.github.com/repos/themw123/jarvis_v2/releases/latest"
        try:
            response = requests.get(api_url)
            latest_release = response.json()
            self.sha = latest_release['tag_name'].replace("Release-", "")
            
            if self.config["version"] == "0":
                self.config["version"] = str(self.sha)
                config_path = os.path.join(self.current_dir, "config.json")
                with open(config_path, 'w') as file:
                    json.dump(self.config, file, indent=4)
                    
            if self.sha != self.config["version"]:
                print(f"\n- update available with sha: {self.sha}")
                
                asset_name = None
                if self.type == "client":
                    if self.os_type == "Windows":
                        asset_name = "windows-client.zip"
                    elif self.os_type == "Linux":
                        asset_name = "linux-client.zip"
                else:
                    asset_name = "windows-backend.zip"
                
                for asset in latest_release['assets']:
                    if asset['name'] == asset_name:
                        return asset['browser_download_url']
                print("\n- could not find a release. Leaving updater...")
                return
            else:
                return None
        except Exception as e:
            print(f"error in checking for updates: {e}")
            return None

    def download_update(self, download_url):
        if self.os_type == "Windows":
            name = "exe.win-amd64-3.11_" + str(self.sha)
        elif self.os_type == "Linux":
            name = "exe.linux-x86_64-3.11_" + str(self.sha)
            
        current_dir = os.path.dirname(os.path.realpath(__file__))
        
        #current_dir = os.path.abspath(os.path.join(current_dir, ".."))
        

        if self.extension != ".py":
            old_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
            current_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", name))
        else:
            current_dir = os.path.abspath(os.path.join(current_dir, "..", "build", name))
        os.makedirs(current_dir, exist_ok=True)
        
        #delete everything to be sure
        shutil.rmtree(current_dir); os.makedirs(current_dir, exist_ok=True)
        
        update_file = os.path.join(current_dir, 'update.zip')
        print("\n- downloading update...")
        response = requests.get(download_url, stream=True)
        
        total_size = int(response.headers.get('content-length', 0))
        chunk_size = 1024
        downloaded_size = 0

        print("")
        with open(update_file, 'wb') as f:
            for data in response.iter_content(chunk_size=chunk_size):
                downloaded_size += len(data)
                f.write(data)
                progress = (downloaded_size / total_size) * 100
                print(f"- progress: {progress:.2f}%", end='\r')
        print("\n\n- download complete")
    
        print("\n- extracting update...")
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            for file in zip_ref.namelist():
                zip_ref.extract(file, path=current_dir)
        print("\n- update extracted")       
        
        
        print("\n- cleaning up...") 
        os.remove(update_file)
        subdirs = [d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))]
        subdir_path = os.path.join(current_dir, subdirs[0])

        for item in os.listdir(subdir_path):
            item_path = os.path.join(subdir_path, item)
            shutil.move(item_path, current_dir)

        if self.os_type == "Linux":
            assisstant_path_linux = os.path.join(current_dir, 'assisstant')
            os.chmod(assisstant_path_linux, 0o755)
        

        os.rmdir(subdir_path)        
        os.rename(os.path.join(current_dir, "example.config.json"), os.path.join(current_dir, "config.json"))
        
        self.config["version"] = str(self.sha)
        with open(os.path.join(current_dir, "config.json"), "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=2, ensure_ascii=False)      

        
        print("\n- update complete, restarting ...")
        time.sleep(2)
                    
        time.sleep(2)
        if self.os_type == "Windows":
            updated_client = os.path.join(current_dir, 'assisstant.exe')
            subprocess.Popen([updated_client, old_dir], creationflags=subprocess.CREATE_NEW_CONSOLE)
            sys.exit()
        elif self.os_type == "Linux":
            updated_client = os.path.join(current_dir, 'assisstant')
            emulators = "gnome-terminal"
            cmd = [emulators, "--", updated_client, old_dir]
            subprocess.Popen(cmd)
            sys.exit()
        print("\n- you can close the current window.")

        
            
          
    
        
