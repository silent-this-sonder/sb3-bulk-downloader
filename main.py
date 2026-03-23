import json
import os
import string
import zipfile
import shutil
import requests
import scratchattach as s3

URL_LENGTH = len("https://scratch.mit.edu/projects/")
# Used to clean up file names
translation_table = str.maketrans("", "", string.punctuation)
# Filters the projects in My Stuff
filter_arg = [
    "all",
    "shared",
    "unshared"
]


def extract_md5exts(node, seen=None):
    if seen is None:
        seen = set()
    if isinstance(node, dict):
        if "md5ext" in node and isinstance(node["md5ext"], str):
            seen.add(node["md5ext"])
        for v in node.values():
            extract_md5exts(v, seen)
    elif isinstance(node, list):
        for item in node:
            extract_md5exts(item, seen)
    return seen


def download_md5ext(md5ext, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    local_name = md5ext.replace("/", "_")
    local_path = os.path.join(out_dir, local_name)

    if os.path.exists(local_path):
        return local_path

    url = f"https://cdn.assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

    return local_path


def process_project_json(project_json_path, asset_dir):
    # asset_dir is the temporary folder for the project to store assets before zipping it up 
    with open(project_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    md5exts = extract_md5exts(data)

    if not md5exts:
        print("\tNo md5ext assets found in project.json")
        return

    for md5ext in sorted(md5exts):
        try:
            downloaded = download_md5ext(md5ext, asset_dir)
            print(f"\tDownloaded asset {md5ext} -> {downloaded}")
        except Exception as e:
            print(f"\tFailed to download {md5ext}: {e}")


def menu(arr):
    # Displays possibly non-String items in a list
    # and asks users to select one
    # returns the index of the actual object in the list
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

def download_image(img_name, img_url, save_dir):


    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    img_data = requests.get(img_url).content
    filename = os.path.join(save_dir, os.path.basename(img_name))
    with open(filename, "wb") as img_f:
        img_f.write(img_data)
    print("Image downloaded successfully: " + img_name)

# SETUP
while True: 
    username = input("Enter username: ")
    password = input("Enter password: ")

    session = None
    if password:
        try:
            session = s3.login(username, password)
        except Exception as e:
            print("Login failed. Try again. Try to not mess up many times or Scratch might flag you as a clanker.")
        else:
            break

    

print("Which projects would you like to download?")
choice = filter_arg[menu(filter_arg)]

# ACTUAL DOWNLOADING
projects = session.mystuff_projects(choice, page=1, sort_by="")
for p in projects:
    print(p.title)
    project = p
    if input("\tDownload? y/n: ") == "y":
        # Get session id and use to load project
        project = session.connect_project(p.id)



        # Make filename
        fn = project.title.translate(translation_table)


        jsonfile = fn + ".json"  # just name it .json because that's what it is, it's not even a real sb3

        # Removes forbidden characters from file name
        fnc = "".join(c for c in fn if c.isalnum() or c in (' ', '.', '_')).rstrip()

        project_id = p.id
        fnc = f"{fnc}_{project_id}" # this way it won't overwrite projects if you have multpile projects
        # with the same name

        # Prevent the file name using reserved names
        reserved_names = {
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
            "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
            "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        }
        if fnc.upper() in reserved_names:
            fnc = f"_{fnc}"

        #i'm not sure if you can have empty titles
        # wait you can so let's do it
        if not fnc:
            fnc = "unnamed project"

        # make folder
        project_dir = os.path.join("downloads", fnc)
        
        os.makedirs(project_dir, exist_ok=True)

        try:
            project.download(
                filename=jsonfile,
                dir=project_dir
            )
        except Exception as e:
            print(f"\tFailed to download project JSON: {e}")
            continue

        # scratchattach's project.download always appends .sb3 to the filename, so the actual file is jsonfile + ".sb3"
        actual_downloaded_file = jsonfile + ".sb3"

        # Check if the file actually downloaded successfully
        if not os.path.exists(os.path.join(project_dir, actual_downloaded_file)):
            print("\tCould not find downloaded project.json. Skipping.")
            continue

        # Rename the downloaded file to project.json
        os.rename(
            os.path.join(project_dir, actual_downloaded_file),
            os.path.join(project_dir, "project.json")
        )

        # Process downloaded project JSON to fetch md5ext assets
        process_project_json(
            os.path.join(project_dir, "project.json"),
            asset_dir=project_dir
        )
        
        #after that function finished, we now have a folder with all the assets (hopefully) so 
        # now it's time to zip it up

        sb3_filename = f"{fnc}.sb3"
        sb3_path = os.path.join("downloads", sb3_filename)
        with zipfile.ZipFile(sb3_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zf.write(file_path, arcname)
                #hopefully this doesn't corrupt the sb3 since sometimes, if the zipping algorithm  as scratch accept isnt the same it can corrupt it

        
        shutil.rmtree(project_dir)

        print(f"Project saved as {sb3_path}")