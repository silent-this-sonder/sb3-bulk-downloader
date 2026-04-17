from threading import Thread
import tkinter as tk
from queue import Queue

import customtkinter as ctk

from main import DownloadController

ctk.set_default_color_theme("assets/scratch-theme.json")

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
        root.after(100, lambda: check_queue(root, q))

class LoginScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q

        self.user_label = ctk.CTkLabel(self, font=master.bold_font, text="Username")
        self.user_entry = ctk.CTkEntry(self, width=204, height=38)
        self.pw_label = ctk.CTkLabel(self, font=master.bold_font, text="Password")
        self.pw_entry = ctk.CTkEntry(self, width=204, height=38, show="*")
        self.login_button = ctk.CTkButton(
            self, font=master.bold_font, text="Sign in",
            width=62, height=43,
            command=self.validate_login
        )

        self.user_label.pack(pady=2)
        self.user_entry.pack(pady=(2, 25))
        self.pw_label.pack(pady=2)
        self.pw_entry.pack(pady=(2, 25))
        self.login_button.pack(pady=10)

    def validate_login(self):
        if self.master == None:
            return
        Thread(
            target=self.master.validate_login,
            args=(self.user_entry.get(), self.pw_entry.get()),
            daemon=True
        ).start()
        check_queue(self.master, self.q)

class ProjectSelectScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q

        self.project_opts = ["all", "shared", "unshared"]
        self.project_label = ctk.CTkLabel(self, text="Projects to Download")

        self.project_filtervar = tk.StringVar(value="Select an option")
        self.project_optmenu = ctk.CTkOptionMenu(self, variable=self.project_filtervar, values=self.project_opts)
        self.project_filtervar.trace_add("write", lambda *args: self.get_project_list(self.project_filtervar.get()))

        self.project_selectall_button = ctk.CTkButton(self, command=self.select_all_projects, text="Select all")

        self.project_checklist = ScrollableChecklist(self, [])
        self.download_button = ctk.CTkButton(
            self, text="Download Selected",
            command=self.download_selected_projects
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

    def download_selected_projects(self):
        if self.master == None:
            return
        
        selected = self.get_selected_projects()
        total_projects = len(selected)
        step_val = 100 * 1 / total_projects

        self.master.switch_screen(self.master.download_screen)
        self.master.download_screen.download_selected_projects(selected, total_projects, step_val)

    def get_selected_projects(self):
        selected = []
        # Loop through the buttons list
        # and the corresponding list of BooleanVars to see which are selected
        for i in range(len(self.project_checklist.buttons)):
            checked_val = self.project_checklist.vars[i].get()
            if checked_val:
                selected.append(i)
                # For debugging: prints the selected projects' titles
                # print(project_checklist.buttons[i].cget("text"))

        # Returns the indexes of the selected projects
        return selected
    
    def get_project_list(self, filter_arg):
        if self.master == None:
            return
        
        print(filter_arg)
        # Scroll the view back to the top instead of keeping current yview
        self.project_checklist._parent_canvas.yview_moveto(0)
        Thread(
            target=self.master.get_project_list,
            args=(filter_arg,),
            daemon=True
        ).start()
        check_queue(self.master, self.q)

class DownloadScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
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

    def download_selected_projects(self, selected, total_projects, step_val):
        self.all_download_label.configure(
            text=f"0 / {total_projects} projects downloaded"
        )

        for i in range(total_projects):
            p_index = selected[i]
            Thread(
                target=self.master.download_project,
                args=(p_index,),
                daemon=True
            ).start()
            check_queue(self.master, self.q)

# GUI APP
class AppGUI(ctk.CTk):
    def __init__(self, fg_color = None, **kwargs):
        super().__init__(fg_color, **kwargs)

        ctk.FontManager.load_font("assets/texgyreheros.gyreheros-regular.otf")
        self.bold_font = ctk.CTkFont(family="TeXGyreHeros", size=13, weight="bold")

        self.title("SB3 Bulk Downloader")
        self.geometry("960x720")

        self.download_controller = DownloadController()
        self.q = Queue()

        self.login_screen = LoginScreen(self.q, self)
        self.project_select_screen = ProjectSelectScreen(self.q, self)
        self.download_screen = DownloadScreen(self.q, self)

        self.current_screen = self.login_screen
        self.current_screen.place(relx=0.5, rely=0.5, anchor="center")

    def switch_screen(self, new_screen : ctk.CTkFrame):
        self.current_screen.place_forget()
        self.current_screen = new_screen
        new_screen.place(relx=0.5, rely=0.5, anchor="center")

    def validate_login(self, username, pw):
        success = self.download_controller.validate_login(username, pw)
        if not success:
            self.q.put(lambda: CTkMessagebox(root, "Login Failed", "Try again. Try not to mess up many times or Scratch might flag you as a clanker."))
            return
        self.q.put(lambda: self.switch_screen(self.project_select_screen))

    def get_project_list(self, filter_arg):
        projects = self.download_controller.get_projects(filter_arg)
        project_names = []
        for project in projects:
            project_names.append(project.title)
        self.q.put(lambda: self.project_select_screen.project_checklist.make_checkbuttons(project_names))

    def download_project(self, p_index):
        download = self.download_controller.download_project(p_index)
        if not download:
            self.q.put(lambda: print("Download failed"))
            return
        # Update progress bar of total projects downloaded
        self.q.put(lambda: print("Download successful"))

root = AppGUI()
root.mainloop()