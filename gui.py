import sys
import time
from threading import Thread
import tkinter as tk
from tkinter import filedialog
from queue import Queue, Empty
from pathlib import Path
 

import customtkinter as ctk
from PIL import Image

from main import DownloadController

def get_default_download_dir() -> Path:
    downloads = Path.home() / "Downloads"
    base_dir = downloads if downloads.exists() else Path.home()
    return base_dir / "Scratch-Projects"

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS_DIR = BASE_DIR / "assets"

ctk.set_default_color_theme(str(ASSETS_DIR / "scratch-theme.json"))
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
logo_pil = Image.open(str(ASSETS_DIR / "logo.png"))
logo_img = ctk.CTkImage(
    light_image=logo_pil, dark_image=logo_pil, size=(200, 200)
)

eye_pil = Image.open(str(ASSETS_DIR / "eye.png"))
eye_img = ctk.CTkImage(
    light_image=eye_pil, dark_image=eye_pil, size=(22, 22)
)

eye2_pil = Image.open(str(ASSETS_DIR / "eye2.png"))
eye_closed_img = ctk.CTkImage(
    light_image=eye2_pil, dark_image=eye2_pil, size=(22, 22)
)

class LoginScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q

        self.main_label = ctk.CTkLabel(self, text="Scratch Project Bulk Downloader", font=ctk.CTkFont(size=30, weight="bold"))

        self.logo_label = ctk.CTkLabel(self, image=logo_img, text="")
        self.user_label = ctk.CTkLabel(self, font=master.bold_font, text="Username")
        self.user_entry = ctk.CTkEntry(self, width=204, height=38)
        self.info_label = ctk.CTkLabel(
            self,
            text="Credentials are only sent to Scratch's servers, and we don't store them.",
            wraplength=250,
            text_color="#4d4d4d"
        )
        self.pw_label = ctk.CTkLabel(self, font=master.bold_font, text="Password")
        self.pw_entry = ctk.CTkEntry(self, width=204, height=38, show="*")
        self.pw_visible = False
        self.pw_toggle_button = ctk.CTkButton(self, image=eye_closed_img, text="", width=26, height=26, fg_color="transparent", hover_color="#d0d0d0", command=self.toggle_password_visibility)
        self.login_button = ctk.CTkButton(self, font=master.bold_font, text="Sign in", width=62, height=43, command=self.validate_login)

        self.main_label.pack(pady=20)
        self.logo_label.pack(pady=20)
        self.info_label.pack(padx=20, pady=(0, 15))
        self.user_label.pack(padx=20, pady=2)
        self.user_entry.pack(padx=20, pady=(2, 10))
        self.pw_label.pack(padx=20, pady=2)
        self.pw_entry.pack(padx=20, pady=(2, 25))
        self.pw_toggle_button.place(in_=self.pw_entry, relx=1.0, rely=0.5, x=5, anchor="w")
        self.login_button.pack(padx=20, pady=(10, 20))




        self.user_entry.bind("<Return>", lambda event: self.validate_login()) # Allows pressing enter to login instead of pressing button
        self.pw_entry.bind("<Return>", lambda event: self.validate_login())
        


    def toggle_password_visibility(self):
        self.pw_visible = not self.pw_visible
        self.pw_entry.configure(show="" if self.pw_visible else "*")
        self.pw_toggle_button.configure(image=eye_img if self.pw_visible else eye_closed_img)

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
        self._project_load_id = 0

        self.project_opts = ["all", "shared", "unshared"]
        self.project_label = ctk.CTkLabel(self, font=master.bold_font, text="Projects to Download")

        self.project_filtervar = tk.StringVar(value="Sort by")
        self.project_optmenu = ctk.CTkOptionMenu(self, variable=self.project_filtervar, values=self.project_opts, width=121, height=46)
        self.project_filtervar.trace_add("write", lambda *args: self.get_project_list(self.project_filtervar.get()))

        self.project_selectall_button = ctk.CTkButton(self, command=self.select_all_projects, font=master.bold_font, text="Select all", width=84, height=31)

        self.project_checklist = ScrollableChecklist(self, [], width=300)
        
        self.skip_existing_var = tk.BooleanVar(value=True)
        self.skip_existing_checkbox = ctk.CTkCheckBox(self, text="Skip already downloaded projects (Resume)", variable=self.skip_existing_var)
        
        self.output_dir = get_default_download_dir()
        self.master.download_controller.output_dir = str(self.output_dir)
        self.output_dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.output_dir_label = ctk.CTkLabel(self.output_dir_frame, text=f"Output: {self.output_dir}", text_color="#4d4d4d", anchor="w")
        self.browse_button = ctk.CTkButton(self.output_dir_frame, text="Browse...", width=60, command=self.browse_output_dir)
        
        self.output_dir_label.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.browse_button.pack(side="right")

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
        self.output_dir_frame.pack(padx=20, pady=(15, 0), fill="x")
        self.download_button.pack(padx=20, pady=15)

    # Select all the projects in the list
    def select_all_projects(self):
        for buttonvar in self.project_checklist.vars:
            buttonvar.set(True)
        self.project_selectall_button.configure(text="Deselect all", command=self.deselect_all_projects)

    def browse_output_dir(self):
        chosen = filedialog.askdirectory(initialdir=str(self.output_dir))
        if chosen:
            self.output_dir = Path(chosen)
            self.output_dir_label.configure(text=f"Output: {chosen}")
            if self.master:
                self.master.download_controller.output_dir = chosen

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
            CTkMessagebox(self, "Nothing selected", "Please select at least one project.")
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
        
        self._project_load_id += 1
        load_id = self._project_load_id

        # print(filter_arg)
        # Scroll the view back to the top instead of keeping current yview
        self.project_checklist._parent_canvas.yview_moveto(0)
        self.project_checklist.make_checkbuttons([])  # clear the list
        self.download_button.configure(state="disabled")
        self.project_label.configure(text="Loading projects...")  # ← loading feedback
        self.project_optmenu.configure(state="disabled")  # prevent new fetches while loading

        Thread(
            target=self.master.get_project_list,
            args=(filter_arg, load_id),
            daemon=True
        ).start()

class DownloadScreen(ctk.CTkFrame):
    def __init__(self, q, master = None, **kwargs):
        super().__init__(master, **kwargs)
        self.q = q
        
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
        self.back_button = ctk.CTkButton(
            self, font=master.bold_font, text="Back to Projects",
            command=self.go_back, state="disabled"
        )
        self.screen_label.pack(padx=20, pady=20)
        self.cur_download_progress.pack(padx=20, pady=(20, 2))
        self.cur_download_label.pack(padx=20)
        self.all_download_progress.pack(padx=20, pady=(30, 2))
        self.all_download_label.pack(padx=20)
        self.back_button.pack(padx=20, pady=20)

    def go_back(self):
        if self.master is not None:
            self.master.switch_screen(self.master.project_select_screen)

    def download_selected_projects(self, selected, total_projects, step_val, skip_existing):
        if total_projects == 0:
            CTkMessagebox(self.master, "Nothing selected", "Please select at least one project.")
            return

        info = self.master.download_controller.progress_bar_info
        info["downloaded_projects"] = 0
        info["total_projects"] = total_projects
        info["downloaded_assets"] = 0
        info["total_assets"] = 0
        info["current_project"] = "Starting..."

        self.back_button.configure(state="disabled")

        self.master.switch_screen(self.master.download_screen)
        self.all_download_label.configure(text=f"0 / {total_projects} projects downloaded")

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
            all_progress = info["processed_projects"] / info["total_projects"]
        else:
            all_progress = 0
            
        self.all_download_progress.set(all_progress)
        self.all_download_label.configure(
            text=f"{info['downloaded_projects']} / {info['total_projects']} projects downloaded"
        )
        
        if info["processed_projects"] < info["total_projects"]:
            self.after(100, self.update_progress)
      

    def on_downloads_completed(self):
        self.cur_download_label.configure(text="Finished downloading!")
        self.all_download_label.configure(text="All projects processed")
        self.back_button.configure(state="normal")


# GUI APP
class AppGUI(ctk.CTk):
    def __init__(self, fg_color = None, **kwargs):
        super().__init__(fg_color, **kwargs)

        ctk.FontManager.load_font(str(ASSETS_DIR / "texgyreheros.gyreheros-regular.otf"))
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
        try: 
            self.iconbitmap(str(ASSETS_DIR / "icon.ico"))
            # this try block is just so that it doesn't error on local runs with the source code or other OS's
            # in reality, this should only affect the compiled version of windows by adding the icon to the taskbar
            
        except:
            pass
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

    def get_project_list(self, filter_arg, load_id):
        is_loading = [True]
        
        def update_loading_label():
            while is_loading[0]:
                try:
                    num_projects = len(self.download_controller.projects)
                    self.q.put(lambda n=num_projects: getattr(self.project_select_screen, 'project_label').configure(text=f"Loading projects... ({n} found)"))
                except Exception:
                    pass
                time.sleep(0.5)

        Thread(target=update_loading_label, daemon=True).start()

        try:
            projects = self.download_controller.get_projects(filter_arg)
            project_names = [project.title for project in projects]

            def update_ui(lid=load_id):
                # Discard result if a newer fetch has already started
                if self.project_select_screen._project_load_id != lid:
                    return
                self.project_select_screen.project_optmenu.configure(state="normal")
                self.project_select_screen.project_label.configure(text="Projects to Download")
                
                self.project_select_screen.project_checklist.make_checkbuttons(project_names)
                if project_names:
                    self.project_select_screen.download_button.configure(state="normal")
                    # this makes the button clickable
                else:
                    self.project_select_screen.download_button.configure(state="disabled")
                    # this makes the button unclickable if there are no projects to download
            self.q.put(update_ui)
        except Exception as e:
            error_msg = str(e)
            def error_ui(lid=load_id):
                if self.project_select_screen._project_load_id != lid:
                    return
                self.project_select_screen.project_optmenu.configure(state="normal")
                self.project_select_screen.project_label.configure(text=f"Error loading projects: {error_msg}")
                self.project_select_screen.project_checklist.make_checkbuttons([])
                self.project_select_screen.download_button.configure(state="disabled")
            self.q.put(error_ui)
        finally:
            is_loading[0] = False

    def download_all_projects(self, selected, total_projects, skip_existing):
        info = self.download_controller.progress_bar_info
        info["downloaded_projects"] = 0
        info["processed_projects"] = 0
        info["total_projects"] = total_projects
        info["downloaded_assets"] = 0
        info["total_assets"] = 0
        info["current_project"] = "Starting..."
        
        for p_index in selected:
            download = self.download_controller.download_project(p_index, skip_existing)
            if not download:
                # retry one more time before giving up
                download = self.download_controller.download_project(p_index, skip_existing)
            if not download:
                self.q.put(lambda idx=p_index: CTkMessagebox(
                    self, "Download Failed",
                    f"Failed to download project at index {idx}. Skipping."
                ))
            info["processed_projects"] += 1
        self.q.put(lambda: self.download_screen.on_downloads_completed())

if __name__ == "__main__":
    root = AppGUI()
    root.mainloop()
