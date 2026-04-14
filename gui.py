from threading import Thread
import tkinter as tk
from tkinter import ttk
from queue import Queue

import customtkinter as ctk

from main import DownloadController

# CUSTOM WIDGETS
class ScrollableChecklist(ctk.CTkScrollableFrame):
    '''Create a list of checkbuttons that supports scrolling'''
    def __init__(self, master, items, **kwargs):
        super().__init__(master, **kwargs)
        self.items = items
        self.buttons = []
        # Populate with checkbuttons
        self.vars = []
        self.make_checkbuttons(items)

    def make_checkbuttons(self, items):
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
            cb = ctk.CTkCheckBox(self, text=item, variable=self.vars[i])
            self.buttons.append(cb)
            cb.pack(anchor="w")

class CTkMessagebox(ctk.CTkToplevel):
    def __init__(self, master : ctk.CTk, title, desc, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        x = master.winfo_x() + (master.winfo_width() // 2) - (300 // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (200 // 2)
        self.geometry(f"300x200+{x}+{y}")
        self.resizable(False, False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.title(title)
        self.label = ctk.CTkLabel(self, text=desc, wraplength=250)
        self.button = ctk.CTkButton(self, text="OK", command=self.destroy)
        self.label.grid(row=0, column=0)
        self.button.grid(row=1, column=0)

        self.grab_set()
        self.master.wait_window(self)

# SCREENS
def check_queue(root : ctk.CTk, q : Queue):
    '''
    Checks the queue for callback functions from the backend tasks and runs it.
    This stops the GUI from waiting and freezing the screen.
    '''
    try:
        callback = q.get_nowait()
        callback()
    except:
        root.after(100, check_queue)

class LoginScreen(ttk.Frame):
    def __init__(self, q, master = None, *, border = ..., borderwidth = ..., class_ = "", cursor = "", height = 0, name = ..., padding = ..., relief = ..., style = "", takefocus = "", width = 0):
        super().__init__(master, border=border, borderwidth=borderwidth, class_=class_, cursor=cursor, height=height, name=name, padding=padding, relief=relief, style=style, takefocus=takefocus, width=width)
        self.q = q
        
        self.user_label = ctk.CTkLabel(self.login_screen, text="Username:")
        self.user_entry = ctk.CTkEntry(self.login_screen)
        self.pw_label = ctk.CTkLabel(self.login_screen, text="Password:")
        self.pw_entry = ctk.CTkEntry(self.login_screen, show="*")
        self.login_button = ctk.CTkButton(
            self.login_screen, text="Login",
            command=validate_login
        )
        self.user_label.pack(pady=5)
        self.user_entry.pack(pady=5)
        self.pw_label.pack(pady=5)
        self.pw_entry.pack(pady=5)
        self.login_button.pack(pady=10)

class ProjectSelectScreen(ttk.Frame):
    def __init__(self, q, master = None, *, border = ..., borderwidth = ..., class_ = "", cursor = "", height = 0, name = ..., padding = ..., relief = ..., style = "", takefocus = "", width = 0):
        super().__init__(master, border=border, borderwidth=borderwidth, class_=class_, cursor=cursor, height=height, name=name, padding=padding, relief=relief, style=style, takefocus=takefocus, width=width)
        self.q = q

        self.project_opts = ["all", "shared", "unshared"]
        self.project_label = ctk.CTkLabel(self.project_select_screen, text="Projects to Download")

        self.project_filtervar = tk.StringVar(value="Select an option")
        self.project_optmenu = ctk.CTkOptionMenu(self.project_select_screen, variable=self.project_filtervar, values=self.project_opts)
        self.project_filtervar.trace_add("write", lambda *args: get_project_list(self.project_filtervar.get()))

        self.project_selectall_button = ctk.CTkButton(self.project_select_screen, command=self.select_all_projects, text="Select all")

        self.project_checklist = ScrollableChecklist(self.project_select_screen, [])
        self.download_button = ctk.CTkButton(
            self.project_select_screen, text="Download Selected",
            command=download_selected_projects
        )

        self.project_label.pack()
        self.project_optmenu.pack()
        self.project_selectall_button.pack()
        self.project_checklist.pack(fill="y", expand=True)
        self.download_button.pack()

    # Select all the projects in the list
    def select_all_projects(self):
        for buttonvar in self.project_checklist.vars:
            buttonvar.set(True)
        self.project_selectall_button.configure(text="Deselect all", command=self.deselect_all_projects)

    # Deselect the projects in the list
    def deselect_all_projects(self):
        for buttonvar in self.project_checklist.vars:
            buttonvar.set(False)
        self.project_selectall_button.configure(text="Select all", command=self.select_all_projects)

class DownloadScreen(ttk.Frame):
    def __init__(self, q, master = None, *, border = ..., borderwidth = ..., class_ = "", cursor = "", height = 0, name = ..., padding = ..., relief = ..., style = "", takefocus = "", width = 0):
        super().__init__(master, border=border, borderwidth=borderwidth, class_=class_, cursor=cursor, height=height, name=name, padding=padding, relief=relief, style=style, takefocus=takefocus, width=width)
        self.q = q
        
        # TODO: change progresbar set() values to be between 0.0 to 1.0 instead of 0 to 100
        # progress bar for current project
        self.cur_download_progress = ctk.CTkProgressBar(
            self, orientation="horizontal", width=500
        )
        # progress bar for all projects
        self.all_download_progress = ctk.CTkProgressBar(
            self, orientation="horizontal", width=500
        )
        # labels for progress
        self.cur_download_label = ctk.CTkLabel(
            self,
            text="Currently downloading [asset title], [num] / [total] assets downloaded"
        )
        self.all_download_label = ctk.CTkLabel(
            self,
            text="Currently downloading [project title], [num] / [total] projects downloaded"
        )
        self.cur_download_progress.pack()
        self.cur_download_label.pack()
        self.all_download_progress.pack()
        self.all_download_label.pack()

# GUI APP
class AppGUI(ctk.CTk):
    def __init__(self, fg_color = None, **kwargs):
        super().__init__(fg_color, **kwargs)
        self.title("SB3 Bulk Downloader")
        self.geometry("960x720")

        self.download_controller = DownloadController()
        self.q = Queue()

        self.login_screen = LoginScreen(self.q)
        self.project_select_screen = ProjectSelectScreen(self.q)
        self.download_screen = DownloadScreen(self.q)

        self.current_screen = self.login_screen
        self.current_screen.pack()

    def _switch_screen(self, new_screen : ttk.Frame):
        self.current_screen.pack_forget()
        self.current_screen = new_screen
        new_screen.pack()

    def _validate_login(self, username, pw, q):
        success = self.download_controller.validate_login(username, pw)
        if not success:
            q.put(lambda: CTkMessagebox(root, "Login Failed", "Try again. Try not to mess up many times or Scratch might flag you as a clanker."))
            return
        q.put(lambda: self._switch_screen(self.project_select_screen))

    def _get_project_list(self, filter_arg, q):
        projects = self.download_controller.get_projects(filter_arg)
        project_names = []
        for project in projects:
            project_names.append(project.title)
        q.put(lambda: self.project_select_screen.project_checklist.make_checkbuttons(project_names))

    def _download_project(self, p_index, q):
        download = self.download_controller.download_project(p_index)
        if not download:
            q.put(lambda: print("Download failed"))
            return
        # Update progress bar of total projects downloaded
        q.put(lambda: print("Download successful"))

root = AppGUI()
root.mainloop()