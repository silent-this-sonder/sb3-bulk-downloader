import json
import os
import shutil
import string
import time as t
import traceback
import zipfile

import requests
import scratchattach as s3

class DownloadController:
    def __init__(self):
        self.session = None

        self.projects = []
        self.progress_bar_info = {
            "project_stepval": 0,
            "asset_stepval": 0,

            "downloaded_projects": 0,
            "total_projects": 0,

            "current_project": "",
            "downloaded_assets": 0,
            "total_assets": 0
        }

        self.translation_table = str.maketrans("", "", string.punctuation)

    # GUI FUNCTIONS (connect to the Tkinter window)
    def validate_login(self, username, password):
        if not (username and password):
            return False
        try:
            self.session = s3.login(username, password)
            print("Login successful!")
            return True
        except Exception as e:
            return False
    
    def get_projects(self, filter_arg="all"):
        self.projects = []
        if filter_arg == "unshared":
            filter_arg = "notshared"
        pagenum = 1
        while True:
            try: 
                projects = self.session.mystuff_projects(filter_arg, page=pagenum, sort_by="")
                self.projects += projects
            except Exception as e:
                # print("the thing broke here's your error:", e)
                # traceback.print_exc()
                break
            pagenum += 1
        
        self.progress_bar_info["total_projects"] = len(self.projects)
        self.progress_bar_info["project_stepval"] = 100 / self.progress_bar_info["total_projects"]
        return self.projects
    
    def get_pbar(self, key):
        return self.progress_bar_info[key]

    def download_project(self, p_index):
        p = self.projects[p_index]
        project = self.session.connect_project(p.id)
        jsonfile, fnc = DownloadController.make_filenames(p, project, self.translation_table)

        # reset progress bar
        self.progress_bar_info["current_project"] = project.title
        self.progress_bar_info["downloaded_assets"] = 0
        self.progress_bar_info["total_assets"] = 0

        # Download and zip the zb3
        download = DownloadController.download_sb3(self.progress_bar_info, project, fnc, jsonfile)
        if not download:
            return False
        project_dir = download
        
        sb3_path = DownloadController.zip_sb3(fnc, project_dir)
        print(f"Project saved as {sb3_path}")
        self.progress_bar_info["downloaded_projects"] += 1

        # sleep 3 seconds so scratch doesn't rate limit
        t.sleep(3)
        return True
    
    # DOWNLOADER FUNCTIONS

    @staticmethod
    def pbar_to_string(pbar_info):
        all_progress = f"Currently downloading {pbar_info['current_project']},"
        all_progress += f" {pbar_info['downloaded_projects']} / {pbar_info['total_projects']}"
        return all_progress

    @staticmethod
    def download_sb3(pbar_info, project, fnc, jsonfile):
        '''Download the project.json and assets from Scratch into a new directory'''
        project_dir = DownloadController.make_sb3_folder(fnc)
        try:
            project.download(
                filename=jsonfile,
                dir=project_dir
            )
        except Exception as e:
            print(f"\tFailed to download project JSON: {e}")
            return False

        # scratchattach's project.download always appends .sb3 to the filename, so the actual file is jsonfile + ".sb3"
        actual_downloaded_file = jsonfile + ".sb3"

        # Check if the file actually downloaded successfully
        if not os.path.exists(os.path.join(project_dir, actual_downloaded_file)):
            print("\tCould not find downloaded project.json. Skipping.")
            return False

        # Rename the downloaded file to project.json
        os.rename(
            os.path.join(project_dir, actual_downloaded_file),
            os.path.join(project_dir, "project.json")
        )

        # Process downloaded project JSON to fetch md5ext assets
        DownloadController.process_project_json(
            pbar_info,
            os.path.join(project_dir, "project.json"),
            asset_dir=project_dir
        )
        return project_dir
    
    @staticmethod
    def make_sb3_folder(fnc):
        '''Make the directory for the new sb3'''
        project_dir = os.path.join("downloads", fnc)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @staticmethod
    def make_filenames(p, project, translation_table):
        '''Remove forbidden characters and return the names for the sb3 files'''
        fn = project.title.translate(translation_table)
        jsonfile = fn + ".json"  # just name it .json because that's what it is, it's not even a real sb3

        # Removes forbidden characters from file name
        fnc = "".join(c for c in fn if c.isalnum() or c in (' ', '.', '_')).rstrip()

        project_id = p.id
        fnc = f"{fnc}_{project_id}" # avoid overwriting projects with identical names

        # Prevent the file name using reserved names
        reserved_names = {
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
            "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
            "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        }
        if fnc.upper() in reserved_names:
            fnc = f"_{fnc}"

        # In case of empty title
        if not fnc:
            fnc = "unnamed project"

        return jsonfile, fnc

    @staticmethod
    def process_project_json(pbar_info, project_json_path, asset_dir):
        '''Download the assets from the project.json'''
        # asset_dir is the temporary folder for the project to store assets before zipping it up 
        with open(project_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        md5exts = DownloadController.extract_md5exts(data)
        pbar_info["total_assets"] = len(md5exts)
        pbar_info["asset_stepval"] = 100 / pbar_info["total_assets"]

        if not md5exts:
            print("\tNo md5ext assets found in project.json")
            return

        for md5ext in sorted(md5exts):
            try:
                downloaded = DownloadController.download_md5ext(md5ext, asset_dir)
                print(f"\tDownloaded asset {md5ext} -> {downloaded}")
                pbar_info["downloaded_assets"] += 1
            except Exception as e:
                print(f"\tFailed to download {md5ext}: {e}")

    @staticmethod
    def extract_md5exts(node, seen=None):
        '''Recursive function that finds and returns all the md5exts from the project.json'''
        if seen is None:
            seen = set()
        if isinstance(node, dict):
            if "md5ext" in node and isinstance(node["md5ext"], str):
                seen.add(node["md5ext"])
            for v in node.values():
                DownloadController.extract_md5exts(v, seen)
        elif isinstance(node, list):
            for item in node:
                DownloadController.extract_md5exts(item, seen)
        return seen

    @staticmethod
    def download_md5ext(md5ext, out_dir):
        '''Get the asset from Scratch and write it to a file'''

        # Set up the directory, file name, and path
        os.makedirs(out_dir, exist_ok=True)
        local_name = md5ext.replace("/", "_") # avoid accidentally making subfolders
        local_path = os.path.join(out_dir, local_name)

        # avoid duplicate downloads
        if os.path.exists(local_path):
            return local_path

        # actually download
        url = f"https://cdn.assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status() # in case of a failed request

        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)

        return local_path

    @staticmethod
    def zip_sb3(fnc, project_dir):
        '''Zip up the completed folder with all the assets'''
        sb3_filename = f"{fnc}.sb3"
        sb3_path = os.path.join("downloads", sb3_filename)
        with zipfile.ZipFile(sb3_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zf.write(file_path, arcname)
                # hopefully this doesn't corrupt the sb3 since sometimes, if the zipping algorithm as scratch accept isnt the same it can corrupt it
        shutil.rmtree(project_dir)
        return sb3_path

# USER INPUT FUNCTIONS

def input_scratch_login():
    '''Log in to Scratch with user and pw; returns the Session object'''
    while True: 
        username = input("Enter username: ")
        password = input("Enter password: ")

        session = None
        if password:
            try:
                session = s3.login(username, password)
                print("Login successful!")
                return session
            except Exception as e:
                print("Login failed. Try again. Try not to mess up many times or Scratch might flag you as a clanker.")
            else:
                return

def menu(arr):
    '''Displays possibly non-String items in a list, asks users to select one, and returns the index of the actual object in the list'''
    for i in range(len(arr)):
        print("\t" + str(i) + ". " + str(arr[i]))
        
    choice = -1
    while not(0 <= int(choice) <= len(arr)-1):
        choice = input("\tEnter the index of your choice: ")
        if not choice.isdigit():
            print("\tInput invalid: index must be a number.")
            choice = -1
            continue
        if not(0 <= int(choice) <= len(arr)-1):
            print("\tInput invalid: index must be in range.")
            
    choice = int(choice)
    return choice

# MAIN
def cli_downloader():
    download_controller = DownloadController()
    print("SB3 BULK DOWNLOADER")

    # Used to clean up file names
    translation_table = str.maketrans("", "", string.punctuation)

    # Log in to scratch
    session = input_scratch_login()

    # Filters the projects in My Stuff
    filter_arg = [
        "all",
        "shared",
        "notshared"
    ]
    print("Which projects would you like to download?")
    choice = filter_arg[menu(filter_arg)]

    # ACTUAL 
    pagenum = 1
    while True:
        try: 
            projects = session.mystuff_projects(choice, page=pagenum, sort_by="")
            
        except Exception as e:
            # print("the thing broke here's your error:", e)
            # traceback.print_exc()
            break
        pagenum += 1
        
    for p in projects:
        # Title and newline for separation
        print("\n")
        print(p.title)
        project = p
        print("Downloading...")

        # Get session id and use to load project
        project = session.connect_project(p.id)
        # Process filename
        jsonfile, fnc = DownloadController.make_filenames(p, project, translation_table)

        # Download and zip the zb3
        print(DownloadController.pbar_to_string(download_controller.progress_bar_info))
        download = DownloadController.download_sb3(download_controller.progress_bar_info, project, fnc, jsonfile)
        if not download:
            continue
        project_dir = download
        
        sb3_path = DownloadController.zip_sb3(fnc, project_dir)
        print(f"Project saved as {sb3_path}")

        # sleep 3 seconds so scratch doesn't rate limit
        t.sleep(3)

    print("\nEnd of project list. There are no more projects to download.")

if __name__ == "__main__":
    cli_downloader()
