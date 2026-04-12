from threading import Thread
import tkinter as tk
from tkinter import ttk
from queue import Queue

import customtkinter as ctk

from main import DownloadController

class ScrollableChecklist(ctk.CTkScrollableFrame):
    '''Create a list of checkbuttons that supports scrolling'''
    def __init__(self, master, items, **kwargs):
        super().__init__(master, **kwargs)
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
class LoginScreen(ttk.Frame):
    def __init__(self, master = None, *, border = ..., borderwidth = ..., class_ = "", cursor = "", height = 0, name = ..., padding = ..., relief = ..., style = "", takefocus = "", width = 0):
        super().__init__(master, border=border, borderwidth=borderwidth, class_=class_, cursor=cursor, height=height, name=name, padding=padding, relief=relief, style=style, takefocus=takefocus, width=width)
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
    def __init__(self, master = None, *, border = ..., borderwidth = ..., class_ = "", cursor = "", height = 0, name = ..., padding = ..., relief = ..., style = "", takefocus = "", width = 0):
        super().__init__(master, border=border, borderwidth=borderwidth, class_=class_, cursor=cursor, height=height, name=name, padding=padding, relief=relief, style=style, takefocus=takefocus, width=width)
        self.project_opts = ["all", "shared", "unshared"]
        self.project_label = ctk.CTkLabel(self.project_select_screen, text="Projects to Download")

        self.project_filtervar = tk.StringVar(value="Select an option")
        self.project_optmenu = ctk.CTkOptionMenu(self.project_select_screen, variable=self.project_filtervar, values=self.project_opts)
        self.project_filtervar.trace_add("write", lambda *args: get_project_list(self.project_filtervar.get()))

        self.project_selectall_button = ctk.CTkButton(self.project_select_screen, command=select_all_projects, text="Select all")

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

class DownloadScreen(ttk.Frame):
    def __init__(self, master = None, *, border = ..., borderwidth = ..., class_ = "", cursor = "", height = 0, name = ..., padding = ..., relief = ..., style = "", takefocus = "", width = 0):
        super().__init__(master, border=border, borderwidth=borderwidth, class_=class_, cursor=cursor, height=height, name=name, padding=padding, relief=relief, style=style, takefocus=takefocus, width=width)
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

# GEOMETRY MANAGER
login_screen.pack()

# APPLICATION EVENT LOOP
root.mainloop()