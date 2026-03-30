import main
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class ScrollableChecklist(tk.Frame):
    '''Create a list of checkbuttons that supports scrolling'''
    def __init__(self, master, items, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)
        
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel scrolling only when mouse is over the widget
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        
        self.items = items
        self.buttons = []
        # Populate with checkbuttons
        self.vars = []
        self._make_checkbuttons(items)

    def _make_checkbuttons(self, items):
        # get rid of old buttons
        for button in self.buttons:
            button.destroy()
        self.items = items
        self.buttons = []
        # Populate with checkbuttons
        self.vars = []
        for i in range(len(self.items)):
            item = self.items[i]
            self.vars.append(tk.BooleanVar(value=False))
            cb = ttk.Checkbutton(self.frame, text=item, variable=self.vars[i])
            self.buttons.append(cb)
            cb.pack(anchor="w")
    
    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            # Windows: delta is multiple of 120; macOS: delta is ±1 or more
            if abs(event.delta) >= 120:
                delta = int(-1 * (event.delta / 120))
            else:
                delta = -1 * event.delta
            self.canvas.yview_scroll(delta, "units")

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

# FUNCTIONALITY
download_controller = main.DownloadController()

# Rudimentary screen switching
def switch_to_project_select():
    login_screen.pack_forget()
    project_select_screen.pack()

def switch_to_download():
    project_select_screen.pack_forget()
    download_screen.pack()

# Select all the projects in the list
def select_all_projects():
    for buttonvar in project_checklist.vars:
        buttonvar.set(True)
    project_selectall_button.config(text="Deselect all", command=deselect_all_projects)

# Deselect the projects in the list
def deselect_all_projects():
    for buttonvar in project_checklist.vars:
        buttonvar.set(False)
    project_selectall_button.config(text="Select all", command=select_all_projects)

# Login validation
def validate_login():
    success = download_controller.validate_login(user_entry.get(), pw_entry.get())
    if not success:
        messagebox.showerror("Login Failed", "Try again. Try not to mess up many times or Scratch might flag you as a clanker.")
        return
    switch_to_project_select()

# Get project list everytime filter is reselected and show in the checklist
def get_project_list(filter):
    # Scroll the view back to the top instead of keeping current yview
    project_checklist.canvas.yview_moveto(0.0)

    # TODO: use .after() instead of doing it synchronously so that the GUI doesn't freeze while waiting for projects to load
    projects = download_controller.get_projects(filter)
    project_names = []
    for project in projects:
        project_names.append(project.title)
    project_checklist._make_checkbuttons(project_names)

# TODO: connect downloading to actual downloading code
# TODO: code for progress bars to update based on info
# TODO: code for progress labels to update based on info

# MAIN WINDOW
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

# LOGIN SCREEN
login_screen = ttk.Frame()
user_label = ttk.Label(login_screen, text="Username:")
user_entry = ttk.Entry(login_screen)
pw_label = ttk.Label(login_screen, text="Password:")
pw_entry = ttk.Entry(login_screen, show="*")
login_button = ttk.Button(
    login_screen, text="Login",
    command=validate_login
)

user_label.pack(pady=5)
user_entry.pack(pady=5)
pw_label.pack(pady=5)
pw_entry.pack(pady=5)
login_button.pack(pady=10)

# PROJECT SELECT
project_select_screen = ttk.Frame()
project_opts = ["Select an option", "all", "shared", "unshared"]
project_label = ttk.Label(project_select_screen, text="Projects to Download")

project_filtervar = tk.StringVar(value="Select an option")
project_optmenu = ttk.OptionMenu(project_select_screen, project_filtervar, *project_opts)
project_filtervar.trace_add("write", lambda *args: get_project_list(project_filtervar.get()))

project_selectall_button = ttk.Button(project_select_screen, command=select_all_projects, text="Select all")

project_checklist = ScrollableChecklist(project_select_screen, [])
download_button = ttk.Button(
    project_select_screen, text="Download Selected",
    command=switch_to_download
)

project_label.pack()
project_optmenu.pack()
project_selectall_button.pack()
project_checklist.pack(fill="y", expand=True)
download_button.pack()

# DOWNLOADING SCREEN
download_screen = ttk.Frame()
# progress bar for current project
cur_download_progress = ttk.Progressbar(
    download_screen, orient="horizontal", length=500, mode="determinate"
)
# progress bar for all projects
all_download_progress = ttk.Progressbar(
    download_screen, orient="horizontal", length=500, mode="determinate"
)
# labels for progress
cur_download_label = ttk.Label(
    download_screen,
    text="Currently downloading [asset title], [num] / [total] assets downloaded"
)
all_download_label = ttk.Label(
    download_screen,
    text="Currently downloading [project title], [num] / [total] projects downloaded"
)

cur_download_progress.pack()
cur_download_label.pack()
all_download_progress.pack()
all_download_label.pack()

# GEOMETRY MANAGER
login_screen.pack()

# APPLICATION EVENT LOOP
root.mainloop()
