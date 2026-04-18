import json
import os
import shutil
import string
import time as t
import traceback
import zipfile
import warnings
import requests
import scratchattach as s3

class DownloadController:
    """In charge of the downloading logic.

    Attributes:
        session: A scratchattach Session object.
        projects: A list of scratchattach Project objects.
        progress_bar_info: A dictionary containing numerical values representing download progress.
    """
    def __init__(self):
        """Initializes a DownloadController object."""
        self.session = None
        self.output_dir = "downloads"

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
        """Attempts to log into Scratch.
        
        Args:
            username: A self-explanatory string.
            password: A self-explanatory string.
        Returns:
            A boolean of whether or not the login was successful.
        """
        warnings.filterwarnings('ignore', category=s3.LoginDataWarning)
        if not (username and password):
            return False
        try:
            self.session = s3.login(username, password)
            return True
        except Exception as e:
            return False
    
    def get_projects(self, filter_arg="all"):
        """Fetches the projects from a user's My Stuff pages.
        
        Args:
            filter_arg: A string that can be either "all", "shared", "unshared", or "notshared".
        Returns:
            A list containing all the My Stuff projects.
        """
        self.projects = []
        if filter_arg == "unshared":
            filter_arg = "notshared"
        pagenum = 1
        while True:
            try: 
                projects = self.session.mystuff_projects(filter_arg, page=pagenum, sort_by="")
                print(f"Found {len(projects)} projects on page {pagenum} with filter '{filter_arg}'")
                self.projects += projects
                print(f"Current amount of projects so far: {len(self.projects)}")
            except Exception as e:
                # print("the thing broke here's your error:", e)
                # traceback.print_exc()
                break
            pagenum += 1
        
        self.progress_bar_info["total_projects"] = len(self.projects)
        self.progress_bar_info["project_stepval"] = 100 / self.progress_bar_info["total_projects"]
        return self.projects
    
    def get_pbar(self, key):
        """Getter method for accessing one of the progress bar values.
        
        Args:
            key: A string that matches up with any of the progress_bar_info keys.
        Returns:
            The int value associated with the given key.
        """
        return self.progress_bar_info[key]

    def download_project(self, p_index, skip_existing=False):
        """Downloads a project from Scratch onto the user's device.
        
        Args:
            p_index: An int corresponding to a project's index from the self.projects list.
            skip_existing: Optional boolean to skip downloading if the project already exists.
        Returns:
            A boolean of whether the download was successful or not.
        """
        p = self.projects[p_index]
        
        if skip_existing:
            # Predict the sb3 path to see if it already exists before making a network request
            fn = p.title.translate(self.translation_table)
            fnc = "".join(c for c in fn if c.isalnum() or c in (' ', '.', '_')).rstrip()
            fnc = f"{fnc}_{p.id}"
            reserved_names = {
                "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
                "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
            }
            if fnc.upper() in reserved_names:
                fnc = f"_{fnc}"
            if not fnc:
                fnc = "unnamed project"
                
            sb3_path = os.path.join(self.output_dir, fnc, f"{fnc}.sb3")
            if os.path.exists(sb3_path):
                self.progress_bar_info["current_project"] = p.title
                self.progress_bar_info["downloaded_assets"] = 1
                self.progress_bar_info["total_assets"] = 1
                self.progress_bar_info["downloaded_projects"] += 1
                print(f"Skipped {fnc}.sb3 (already exists)")
                return True

        project = self.session.connect_project(p.id)
        jsonfile, fnc = DownloadController.make_filenames(p, project, self.translation_table)

        # reset progress bar
        self.progress_bar_info["current_project"] = project.title
        self.progress_bar_info["downloaded_assets"] = 0
        self.progress_bar_info["total_assets"] = 0

        # print the progress bar (for CLI)
        print(DownloadController.pbar_to_string(self.progress_bar_info))

        # Download and zip the zb3
        download = DownloadController.download_sb3(self.progress_bar_info, project, fnc, jsonfile, self.output_dir)
        if not download:
            return False
        project_dir = download
        
       
        
        sb3_path = DownloadController.zip_sb3(fnc, project_dir)
        print(f"Project saved as {sb3_path}")
        
        # Add metadata and thumbnail after zipping so they sit alongside the sb3
        self.add_metadata(os.path.dirname(sb3_path), p, project)
        self.progress_bar_info["downloaded_assets"] += 1
        
        self.download_thumbnail(project, os.path.dirname(sb3_path))
        self.progress_bar_info["downloaded_assets"] += 1
        
        self.progress_bar_info["downloaded_projects"] += 1

        # sleep 3 seconds so scratch doesn't rate limit
        t.sleep(3)
        return True
    
    def add_metadata(self, project_folder, p, project):
        """Add metadata files alongside the downloaded project.
        
        Args:
            project_folder: The directory where the sb3 file was saved.
            p: The project entry from self.projects.
            project: The connected scratchattach Project object.
        """
        # usually i would've used a txt file for this
        # but i guess a markdown file is better especially now that microslop has added support for it in notepa- i mean sloppad
        metadata_path = os.path.join(project_folder, "metadata.md")
        
        remix_info = ""
        if project.remix_parent is not None:
            remix_info = f"\n**Remix of**: [{project.remix_parent}](https://scratch.mit.edu/projects/{project.remix_parent}/)\n"
            # In scratchattach, project.remix_parent is typically just the parent project ID or None

        with open(metadata_path, "w", encoding="utf-8") as f:
            content = f"""# {project.title}

## Basic Info            

**Project ID**: {p.id}

**Created by**: {project.author().username}

**Shared**: {'Yes' if project.is_shared else 'No'}

**Created on**: {project.created}

**Last modified**: {project.last_modified}

**Share Date**: {project.share_date}

**Original URL**: {project.url}
{remix_info}
**Comments Allowed**: {'Yes' if project.comments_allowed else 'No'}

## Instructions
{project.instructions}

## Notes and Credits
{project.notes}

## Project Statistics

👁️ **Views**: {project.views}
❤️ **Loves**: {project.loves}
⭐ **Favorites**: {project.favorites}
 
"""
            f.write(content)
            
            try:
                comments = project.comments(limit=200, offset=0)
                if comments:
                    f.write("\n## Comments\n\n")
                    for comment in comments:
                        f.write(f"**{comment.author_name}**: {comment.content}\n\n")
                        
                        if getattr(comment, 'reply_count', 0) > 0:
                            replies = comment.replies()
                            for reply in replies:
                                f.write(f"> **{reply.author_name}**: {reply.content}\n\n")
            except Exception as e:
                f.write(f"\n## Comments\n\n*Failed to load comments: {e}*\n\n")

    def download_thumbnail(self, project, out_dir):
        """Downloads the thumbnail for a project.
        
        Args:
            project: A scratchattach Project object.
            out_dir: The directory to download the thumbnail to.
            """
        thumb = project.thumbnail_url
        if thumb:
            try:
                r = requests.get(thumb, stream=True, timeout=30)
                r.raise_for_status()
                thumb_path = os.path.join(out_dir, "thumbnail.png")
                with open(thumb_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)
            except Exception as e:
                print(f"\tFailed to download thumbnail: {e}")


    
    # DOWNLOADER FUNCTIONS

    @staticmethod
    def pbar_to_string(pbar_info):
        """Turns the progress bar numerical values into a text format.
        
        Args:
            pbar_info: A dictionary containing the progress bar numbers.
        Returns:
            A string showing the current download and the amount of finished downloads out of total projects to download.
        """
        all_progress = f"Currently downloading {pbar_info['current_project']},"
        all_progress += f" {pbar_info['downloaded_projects']} / {pbar_info['total_projects']}"
        all_progress += " projects downloaded"
        return all_progress

    @staticmethod
    def download_sb3(pbar_info, project, fnc, jsonfile, output_dir):
        """Downloads the project.json and assets from Scratch into a new directory.
        
        Args:
            pbar_info: A dictionary containing the progress bar numerical values.
            project: A scratchattach Project object to download.
            fnc: A string of the filename for the downloaded sb3 file.
            jsonfile: A string of the project.json filename.
            output_dir: The base directory where the project folder should be created.
        Returns:
            The path to the directory containing the project assets.
        """
        project_dir = DownloadController.make_sb3_folder(fnc, output_dir)
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
        os.replace(
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
    def make_sb3_folder(fnc, output_dir):
        """Makes the directory for the new sb3.
        
        Args:
            fnc: A string of the filename for the downloaded sb3 file.
            output_dir: The directory where the sb3 folder should be created.
        Returns:
            The path to the directory that will store the project assets.
        """
        project_dir = os.path.join(output_dir, fnc, "temp_assets")
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @staticmethod
    def make_filenames(p, project, translation_table):
        """Removes forbidden characters and return the names for the sb3 files.
        
        Args:
            project: A string of the project's original title.
            translation_table: A translation table to remove some forbidden characters.
        Returns:
            jsonfile: A string of the project's project.json filename.
            fnc: A string of the fully cleaned-up file name.
        """
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
        """Extracts the assets from the project.json and downloads them from Scratch.
        
        Args:
            pbar_info: A dict containing the progress bar's numerical values.
            project_json_path: The path...to the project.json??? it's not that hard.
            asset_dir: The temporary folder for storing downloaded assets.
        """
        with open(project_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        md5exts = DownloadController.extract_md5exts(data)
        # Adding 2 extra assets to total for the metadata and thumbnail we make later!
        pbar_info["total_assets"] = len(md5exts) + 2
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
        """Finds and returns all the md5exts from the project.json.
        
        Args:
            node: A dictionary or list to search through.
            seen: A set containing the md5exts.
        Returns:
            The set of all the md5exts.
        """
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
        """Gets an asset from Scratch and writes it to a file.
        
        Args:
            md5ext: A string of the md5ext to fetch.
            out_dir: The directory to download the md5ext to.
        Returns:
            The path to the downloaded asset.
        """

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
        """Zips up the completed project folder into an sb3.
        
        Args:
            fnc: A string of the project's file name.
            project_dir: The directory to zip up.
        Returns:
            The path to the finished sb3 file.
        """
        parent_dir = os.path.dirname(project_dir)
        sb3_filename = f"{fnc}.sb3"
        sb3_path = os.path.join(parent_dir, sb3_filename)
        with zipfile.ZipFile(sb3_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zf.write(file_path, arcname)
                # hopefully this doesn't corrupt the sb3 since sometimes, if the zipping algorithm as scratch accept isnt the same it can corrupt it
        shutil.rmtree(project_dir)
        


        return sb3_path
    
    

class CLIDownloader(DownloadController):
    """Both the view and controller for the CLI downloader."""
    def __init__(self):
        """Intitializes a CLIDownloader object, inheriting from the DownloadController class."""
        super().__init__()

        print("SB3 BULK DOWNLOADER")
        self.input_login()

        # Filters the projects in My Stuff
        filter_arg = [
            "all",
            "shared",
            "notshared"
        ]
        print("Which projects would you like to download?")
        choice = filter_arg[self.menu(filter_arg)]

        self.get_projects(choice)
        for p_index in range(len(self.projects)):
            print("\n")
            self.download_project(p_index)
            # sleep 3 seconds so scratch doesn't rate limit
            t.sleep(3)

        print(f"\n{self.progress_bar_info['downloaded_projects']} / {self.progress_bar_info['total_projects']} projects downloaded")

    def input_login(self):
        """Get and validate the user's username and password."""
        while True: 
            username = input("Enter username: ")
            password = input("Enter password: ")
            if self.validate_login(username, password):
                print("Login successful!")
                break
            print("Login failed. Try again. Try not to mess up many times or Scratch might flag you as a clanker.")
    
    def menu(self, arr):
        '''Displays items in a list for the user to choose from.
        
        Args:
            arr: The list of options.
        Returns:
            The index of the user's choice from the list.
        '''
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

if __name__ == "__main__":
    cli_downloader = CLIDownloader()
