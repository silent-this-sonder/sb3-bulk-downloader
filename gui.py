import tkinter as tk
from tkinter import ttk

class ScrollableChecklist(tk.Frame):
    '''Create a list of checkbuttons that supports scrolling'''
    def __init__(self, master, items, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = tk.Frame(self.canvas)
        
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Populate with checkbuttons
        self.vars = {}
        for item in items:
            var = tk.IntVar()
            cb = tk.Checkbutton(self.frame, text=item, variable=var)
            cb.pack(anchor="w")
            self.vars[item] = var

# MAIN WINDOW
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

# WIDGETS

# Login Screen
user_label = tk.Label(root, text="Username:")
user_entry = tk.Entry(root)
pw_label = tk.Label(root, text="Password:")
pw_entry = tk.Entry(root, show="*")
login_button = tk.Button(root, text="Login")

# Project Filtering
project_opts = ["all", "shared", "unshared"]
project_label = tk.Label(root, text="Projects to Download")
project_optmenu = tk.OptionMenu(root, tk.StringVar(value="all"), *project_opts)
project_selectall_button = tk.Button(root, text="Select all")
project_checklist = ScrollableChecklist(root, ["example"] * 50)

# Downloading
download_button = tk.Button(root, text="Download Selected")
# progress bar for current project
cur_download_progress = ttk.Progressbar(
    root, orient="horizontal", length=500, mode="determinate"
)
# progress bar for all projects
all_download_progress = ttk.Progressbar(
    root, orient="horizontal", length=500, mode="determinate"
)
# labels for progress
cur_download_label = tk.Label(
    root,
    text="Currently downloading [asset title], [num] / [total] assets downloaded"
)
all_download_label = tk.Label(
    root,
    text="Currently downloading [project title], [num] / [total] projects downloaded"
)

# FUNCTIONALITY

# TODO: I want to organize the tkinter gui file a bit and make it only handle the widget display
    # The code should be modular to keep it very neat
    # I don't have the structure fully fleshed out yet but according to TkinterBuilder,
    # they turn the gui file into a class so that the main file can just pass in data
    # and receive output from the gui, which sounds pretty good.
# TODO: make "Select all" actually select all
# TODO: get project list everytime filter is reselected and show in the checklist
# TODO: connect downloading to actual downloading code
# TODO: code for progress bars to update based on info
# TODO: code for progress labels to update based on info

# GEOMETRY MANAGER

# Login Screen
user_label.pack()
user_entry.pack()
pw_label.pack()
pw_entry.pack()
login_button.pack()

# Project Filtering
project_label.pack()
project_optmenu.pack()
project_selectall_button.pack()
project_checklist.pack(fill="y", expand=True)

# Downloading
download_button.pack()
cur_download_progress.pack()
cur_download_label.pack()
all_download_progress.pack()
all_download_label.pack()

# APPLICATION EVENT LOOP
root.mainloop()
