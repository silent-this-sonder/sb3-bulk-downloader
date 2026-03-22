import json
import requests
import scratchattach as s3
import string
import os

URL_LENGTH = len("https://scratch.mit.edu/projects/")
# Used to clean up file names
translation_table = str.maketrans("", "", string.punctuation)
# Filters the projects in My Stuff
filter_arg = [
    "all",
    "shared",
    "unshared"
]

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
    # Downloads the image from a specified url

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    img_data = requests.get(img_url).content
    filename = os.path.join(save_dir, os.path.basename(img_name))
    with open(filename, "wb") as img_f:
        img_f.write(img_data)
    print("Image downloaded successfully: " + img_name)

# SETUP
username = input("Enter username: ")
password = input("Enter password: ")
session = s3.login(username, password)

print("Which projects would you like to download?")
choice = filter_arg[menu(filter_arg)]

# ACTUAL DOWNLOADING
projects = projects = session.mystuff_projects(choice, page=1, sort_by="")
for p in projects:
    print(p["title"])
    project = p
    if input("\tDownload? y/n: ") == "y":
        # Get session id and use to load project
        project = session.connect_project(p["url"][URL_LENGTH:])



        # Make filename
        fn = project.title.translate(translation_table)
        sb3 =  fn + ".sb3" # put the sb3 in a separate bar so we do filesystem stuff with the filename

        # Removes forbidden characters from file name
        fnc = "".join(c for c in fn if c.isalnum() or c in (' ', '.', '_')).rstrip() 
        
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
            
            #for some reason python interprets non-strings as false when used as a boolean so 
            # we can use that to our advantage and rename it to unnamed project instead
        
        # make folder
        project_dir = os.path.join("downloads", fnc)
        os.makedirs(project_dir, exist_ok=True)


        # TODO: loop through assets and download
        # TODO: save each project in it's own folder
        # with a README/instructions.txt containing all relevant metadata that Scratchattach lets us access
        # TODO: save all comments in comments.txt
        # TODO: save thumbnail by getting url and using fetch request

        project.download(
            filename=fnc,
            dir=project_dir
        )
        print("\tDownloaded as " + fn + "!")