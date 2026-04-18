import sys
from threading import Thread
import tkinter as tk
from queue import Queue, Empty
import ctypes

import customtkinter as ctk
from PIL import Image

from main import DownloadController

ctk.set_default_color_theme("assets/scratch-theme.json")
ctk.set_appearance_mode("system")

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
            cb.pack(pady=2, anchor="w")

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
logo_pil = Image.open("assets/logo.png")
logo_img = ctk.CTkImage(
    light_image=logo_pil, dark_image=logo_pil, size=(200, 200)
)

class LoginScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q

        self.logo_label = ctk.CTkLabel(self, image=logo_img, text="")
        self.user_label = ctk.CTkLabel(self, font=master.bold_font, text="Username")
        self.user_entry = ctk.CTkEntry(self, width=204, height=38)
        self.pw_label = ctk.CTkLabel(self, font=master.bold_font, text="Password")
        self.pw_entry = ctk.CTkEntry(self, width=204, height=38, show="*")
        self.login_button = ctk.CTkButton(
            self, font=master.bold_font, text="Sign in",
            width=62, height=43,
            command=self.validate_login
        )

        self.logo_label.pack(pady=20)
        self.user_label.pack(padx=20, pady=2)
        self.user_entry.pack(padx=20, pady=(2, 25))
        self.pw_label.pack(padx=20, pady=2)
        self.pw_entry.pack(padx=20, pady=(2, 25))
        self.login_button.pack(padx=20, pady=(10, 20))

        self.user_entry.bind("<Return>", lambda event: self.validate_login()) # Allows pressing enter to login instead of pressing button
        self.pw_entry.bind("<Return>", lambda event: self.validate_login())


    def validate_login(self):
        if self.master is None:
            return
        Thread(
            target=self.master.validate_login,
            args=(self.user_entry.get(), self.pw_entry.get()),
            daemon=True
        ).start()

class ProjectSelectScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q

        self.project_opts = ["all", "shared", "unshared"]
        self.project_label = ctk.CTkLabel(self, font=master.bold_font, text="Projects to Download")

        self.project_filtervar = tk.StringVar(value="Sort by")
        self.project_optmenu = ctk.CTkOptionMenu(self, variable=self.project_filtervar, values=self.project_opts, width=121, height=46)
        self.project_filtervar.trace_add("write", lambda *args: self.get_project_list(self.project_filtervar.get()))

        self.project_selectall_button = ctk.CTkButton(self, command=self.select_all_projects, font=master.bold_font, text="Select all", width=84, height=31)

        self.project_checklist = ScrollableChecklist(self, [], width=300)
        
        self.skip_existing_var = tk.BooleanVar(value=True)
        self.skip_existing_checkbox = ctk.CTkCheckBox(self, text="Skip already downloaded projects (Resume)", variable=self.skip_existing_var)
        
        self.download_button = ctk.CTkButton(
            self, font=master.bold_font, text="Download selected",
            command=self.download_selected_projects,
            width=84, height=31, state="disabled"
        )

        self.project_label.pack(padx=20, pady=20)
        self.project_optmenu.pack(padx=20, pady=10)
        self.project_selectall_button.pack(padx=20, pady=(0, 10))
        self.project_checklist.pack(padx=20, fill="y", expand=True)
        self.skip_existing_checkbox.pack(padx=20, pady=(10, 0))
        self.download_button.pack(padx=20, pady=20)

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
        if self.master is None:
            return
        selected = self.get_selected_projects()
        total_projects = len(selected)

        if total_projects == 0:
            return
    
        step_val = 1.0 / total_projects
        
        self.master.switch_screen(self.master.download_screen)
        self.master.download_screen.download_selected_projects(selected, total_projects, step_val, self.skip_existing_var.get())

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
        if self.master is None:
            return
        
        # print(filter_arg)
        # Scroll the view back to the top instead of keeping current yview
        self.project_checklist._parent_canvas.yview_moveto(0)
        Thread(
            target=self.master.get_project_list,
            args=(filter_arg,),
            daemon=True
        ).start()

class DownloadScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q
        
        # TODO: change progresbar set() values to be between 0.0 to 1.0 instead of 0 to 100
        self.screen_label = ctk.CTkLabel(
            self, font=master.bold_font,
            text="Download in Progress"
        )
        # progress bar for current project
        self.cur_download_progress = ctk.CTkProgressBar(
            self, orientation="horizontal",
            width=500, height=40
        )
        # progress bar for all projects
        self.all_download_progress = ctk.CTkProgressBar(
            self, orientation="horizontal",
            width=500, height=40
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
        self.screen_label.pack(padx=20, pady=20)
        self.cur_download_progress.pack(padx=20, pady=(20, 2))
        self.cur_download_label.pack(padx=20)
        self.all_download_progress.pack(padx=20, pady=(30, 2))
        self.all_download_label.pack(padx=20)

    def download_selected_projects(self, selected, total_projects, step_val, skip_existing):
        if total_projects == 0:
            return
        self.all_download_label.configure(
            text=f"0 / {total_projects} projects downloaded"
        )

        Thread(
            target=self.master.download_all_projects,
            args=(selected, total_projects, skip_existing),
            daemon=True
        ).start()
        
        self.update_progress()

    def update_progress(self):
        if self.master is None:
            return
            
        info = self.master.download_controller.progress_bar_info
        
        # update current project progress
        if info["total_assets"] > 0:
            cur_progress = info["downloaded_assets"] / info["total_assets"]
        else:
            cur_progress = 0
        self.cur_download_progress.set(cur_progress)
        self.cur_download_label.configure(
            text=f"Currently downloading {info['current_project']}, {info['downloaded_assets']} / {info['total_assets']} assets downloaded"
        )
        
        # update all projects progress
        if info["total_projects"] > 0:
            all_progress = info["downloaded_projects"] / info["total_projects"]
        else:
            all_progress = 0
            
        self.all_download_progress.set(all_progress)
        self.all_download_label.configure(
            text=f"{info['downloaded_projects']} / {info['total_projects']} projects downloaded"
        )
        
        if info["downloaded_projects"] < info["total_projects"]:
            self.after(100, self.update_progress)
        else:
            self.cur_download_label.configure(text="Finished downloading!")

# GUI APP
class AppGUI(ctk.CTk):
    def __init__(self, fg_color = None, **kwargs):
        super().__init__(fg_color, **kwargs)

        ctk.FontManager.load_font("assets/texgyreheros.gyreheros-regular.otf")
        self.bold_font = ctk.CTkFont(family="TeXGyreHeros", size=13, weight="bold")

        self.title("SB3 Bulk Downloader")
        w = 960
        h = 720
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.download_controller = DownloadController()
        self.q = Queue()

        self.login_screen = LoginScreen(self.q, self)
        self.project_select_screen = ProjectSelectScreen(self.q, self)
        self.download_screen = DownloadScreen(self.q, self)

        self.current_screen = self.login_screen
        self.current_screen.place(relx=0.5, rely=0.5, anchor="center")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.queue_loop()

    def queue_loop(self):
        try:
            while True:
                callback = self.q.get_nowait()
                callback()
        except Empty:
            pass

        self.after(100, self.queue_loop)

    def on_closing(self):
        '''Here we see a lovely function for manually closing this app window because Python is a hard-headed mule :D
        '''
        self.destroy()
        sys.exit()

    def switch_screen(self, new_screen : ctk.CTkFrame):
        self.current_screen.place_forget()
        self.current_screen = new_screen
        new_screen.place(relx=0.5, rely=0.5, anchor="center")

    def validate_login(self, username, pw):
        success = self.download_controller.validate_login(username, pw)
        if not success:
            self.q.put(lambda: CTkMessagebox(self, "Login Failed", "Try again. Try not to mess up many times or Scratch might flag you as a clanker."))
            return
        self.q.put(lambda: self.switch_screen(self.project_select_screen))

    def get_project_list(self, filter_arg):
        projects = self.download_controller.get_projects(filter_arg)
        project_names = [project.title for project in projects]

        def update_ui():
            self.project_select_screen.project_checklist.make_checkbuttons(project_names)
            if project_names:
                self.project_select_screen.download_button.configure(state="normal")
                # this makes the button clickable
            else:
                self.project_select_screen.download_button.configure(state="disabled")
                # this makes the button unclickable if there are no projects to download
        self.q.put(update_ui)

    def download_all_projects(self, selected, total_projects, skip_existing):
        info = self.download_controller.progress_bar_info
        info["downloaded_projects"] = 0
        info["total_projects"] = total_projects
        info["downloaded_assets"] = 0
        info["total_assets"] = 0
        info["current_project"] = "Starting..."
        
        for p_index in selected:
            download = self.download_controller.download_project(p_index, skip_existing)
            if not download:
                self.q.put(lambda idx=p_index: print(f"Download failed for index {idx}"))
                continue
        self.q.put(lambda: print("All downloads completed!"))

root = AppGUI()
root.mainloop()
