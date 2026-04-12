import main
# Tkinter imports
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
# import threading stuff to run the backend work
from threading import Thread
from queue import Queue

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

# BACKEND STUFF
download_controller = main.DownloadController()

def _validate_login(username, pw, q):
    success = download_controller.validate_login(username, pw)
    if not success:
        q.put(lambda: messagebox.showerror(
            "Login Failed",
            "Try again. Try not to mess up many times or Scratch might flag you as a clanker."
        ))
        return
    q.put(lambda: switch_to_project_select())

def _get_project_list(filter_arg, q):
    projects = download_controller.get_projects(filter_arg)
    project_names = []
    for project in projects:
        project_names.append(project.title)
    q.put(lambda: project_checklist._make_checkbuttons(project_names))

def _download_project(p_index, q):
    download = download_controller.download_project(p_index)
    if not download:
        q.put(lambda: print("Download failed"))
        return
    # Update progress bar of total projects downloaded
    q.put(lambda: print("Download successful"))

def check_queue():
    '''
    Checks the queue for callback functions from the backend tasks and runs it.
    This stops the GUI from waiting and freezing the screen.
    '''
    try:
        callback = q.get_nowait()
        callback()
    except:
        root.after(100, check_queue)

# GUI FUNCTIONS
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
    Thread(
        target=_validate_login,
        args=(user_entry.get(), pw_entry.get(),q),
        daemon=True
    ).start()
    check_queue()

# Get project list everytime filter is reselected and show in the checklist
def get_project_list(filter_arg):
    # Scroll the view back to the top instead of keeping current yview
    project_checklist.canvas.yview_moveto(0.0)
    Thread(
        target=_get_project_list,
        args=(filter_arg, q),
        daemon=True
    ).start()
    check_queue()

def get_selected_projects():
    selected = []
    # Loop through the buttons list
    # and the corresponding list of BooleanVars to see which are selected
    for i in range(len(project_checklist.buttons)):
        checked_val = project_checklist.vars[i].get()
        if checked_val:
            selected.append(i)
            # For debugging: prints the selected projects' titles
            # print(project_checklist.buttons[i].cget("text"))

    # Returns the indexes of the selected projects
    return selected

def download_selected_projects():
    selected = get_selected_projects()
    total_projects = len(selected)
    step_val = 100 * 1 / total_projects

    switch_to_download()
    all_download_label.config(
        text=f"0 / {total_projects} projects downloaded"
    )

    for i in range(total_projects):
        p_index = selected[i]
        Thread(
            target=_download_project,
            args=(p_index, q),
            daemon=True
        ).start()
        check_queue()

# MAIN WINDOW
root = tk.Tk()
root.title("SB3 Bulk Downloader")
root.geometry("960x720")

q = Queue()

# LOGIN SCREEN
login_screen = ttk.Frame()
login_screen.grid_rowconfigure(0, weight=1)
login_screen.grid_columnconfigure(0, weight=1)
login_screen.grid(row=0, column=0, sticky="nsew")

user_label = ttk.Label(login_screen, text="Username:")
user_entry = ttk.Entry(login_screen)
pw_label = ttk.Label(login_screen, text="Password:")
pw_entry = ttk.Entry(login_screen, show="*")
login_button = ttk.Button(
    login_screen, text="Login",
    command=validate_login
)

user_label.grid(row=0, column=0)
user_entry.grid(row=1, column=0)
pw_label.grid(row=2, column=0)
pw_entry.grid(row=3, column=0)
login_button.grid(row=4, column=0)

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
    command=download_selected_projects
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
