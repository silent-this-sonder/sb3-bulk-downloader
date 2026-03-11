import string
import scratchattach as s3

# Used to get project id from url
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
        fn += ".sb3"

        project.download(
            filename=fn,
            dir="downloads/"
        )
        print("\tDownloaded as " + fn + "!")