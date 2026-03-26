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

        # Bind mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows/macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)    # Linux scroll down
        
        # Populate with checkbuttons
        self.vars = {}
        for item in items:
            var = tk.IntVar()
            cb = tk.Checkbutton(self.frame, text=item, variable=var)
            cb.pack(anchor="w")
            self.vars[item] = var

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

# MAIN WINDOW
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

# Rudimentary screen switching
def switch_to_project_select():
    login_screen.pack_forget()
    project_select_screen.pack()

def switch_to_download():
    project_select_screen.pack_forget()
    download_screen.pack()

# LOGIN SCREEN
login_screen = tk.Frame()
user_label = tk.Label(login_screen, text="Username:")
user_entry = tk.Entry(login_screen)
pw_label = tk.Label(login_screen, text="Password:")
pw_entry = tk.Entry(login_screen, show="*")
login_button = tk.Button(
    login_screen, text="Login",
    command=switch_to_project_select
)

user_label.pack()
user_entry.pack()
pw_label.pack()
pw_entry.pack()
login_button.pack()

# PROJECT SELECT
project_select_screen = tk.Frame()
project_opts = ["all", "shared", "unshared"]
project_label = tk.Label(project_select_screen, text="Projects to Download")
project_filtervar = tk.StringVar(value="all")
project_optmenu = tk.OptionMenu(project_select_screen, project_filtervar, *project_opts)
project_selectall_button = tk.Button(project_select_screen, text="Select all")
project_checklist = ScrollableChecklist(project_select_screen, ["example"] * 50)
download_button = tk.Button(
    project_select_screen, text="Download Selected",
    command=switch_to_download
)

project_label.pack()
project_optmenu.pack()
project_selectall_button.pack()
project_checklist.pack(fill="y", expand=True)
download_button.pack()

# DOWNLOADING SCREEN
download_screen = tk.Frame()
# progress bar for current project
cur_download_progress = ttk.Progressbar(
    download_screen, orient="horizontal", length=500, mode="determinate"
)
# progress bar for all projects
all_download_progress = ttk.Progressbar(
    download_screen, orient="horizontal", length=500, mode="determinate"
)
# labels for progress
cur_download_label = tk.Label(
    download_screen,
    text="Currently downloading [asset title], [num] / [total] assets downloaded"
)
all_download_label = tk.Label(
    download_screen,
    text="Currently downloading [project title], [num] / [total] projects downloaded"
)

cur_download_progress.pack()
cur_download_label.pack()
all_download_progress.pack()
all_download_label.pack()

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
login_screen.pack()

# APPLICATION EVENT LOOP
root.mainloop()
