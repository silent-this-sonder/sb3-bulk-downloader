from pathlib import Path
import sys

import flet as ft

import main as app_main

def get_default_download_dir() -> Path:
    downloads = Path.home() / "Downloads"
    base_dir = downloads if downloads.exists() else Path.home()
    return base_dir / "Scratch-Projects"

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS_DIR = BASE_DIR / "assets"

# TODO: look at old tkinter code and make sure all functionality is there
DOWNLOAD_CONTROLLER = app_main.DownloadController()
# there's probably like a much better way to do this but i'll fix it later
download_args = {
    "selected": None,
    "total_projects": None,
    "step_val": None,
    "skip_existing": None
}

class LoginScreen(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/login")
        self.main_page = page
        self.horizontal_alignment = "center"
        self.vertical_alignment = "center"

        self.fail_counter = 0
        self.empty_counter = 0

        self.logo_image = ft.Image(
            src=str(ASSETS_DIR / "logo.png"),
            width=200,
            height=200,
            fit="contain",
        )
        self.sb_text = ft.Text(
            "Scratch Project Bulk Downloader",
            size=32,
            weight="w600"
        )
        self.disclaimer  = ft.Text(
            "Credentials are only sent to Scratch's servers, and we don't store them.",
            size=12,
            color="grey600"
        )
        self.login_btn = ft.Button(
            content="Sign in",
            on_click=self.handle_login,
            color="white",
            bgcolor="#855cd6"
        )
        self.username_field = ft.TextField(
            label="Username",
            hint_text="Enter a Scratch username",
            on_submit=self.handle_login
        )
        self.password_field = ft.TextField(
            label="Password",
            hint_text="Enter your password",
            password=True, can_reveal_password=True,
            on_submit=self.handle_login
        )

        self.controls = [
            self.logo_image,
            self.sb_text,
            self.disclaimer,
            self.username_field,
            self.password_field,
            self.login_btn
        ]

    async def handle_login(self, e):
        # just for the funsies
        with open("assets/login_messages.txt", "r", encoding="utf-8") as f:
            login_messages = f.readlines()

        # check if someone made it empty so it doesn't keep sending fail requests to scratch and get flagged or smth
        if self.empty_counter < len(login_messages) and (not self.username_field.value or not self.password_field.value):
            dlg = ft.AlertDialog(
                title="Login Failed",
                content=ft.Text(login_messages[self.empty_counter]),
                actions=[ft.Button("OK", on_click=lambda e: self.main_page.pop_dialog())],
                on_dismiss=lambda e: None
            )
            self.main_page.show_dialog(dlg)
            self.empty_counter += 1
            return

        success = DOWNLOAD_CONTROLLER.validate_login(self.username_field.value, self.password_field.value)
        if not success:
            self.fail_counter += 1
            if self.fail_counter >= 4:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("Are you guessing passwords or something? Please type valid Scratch Account credentials. If you keep messing up, your IP might get banned by Scratch."),
                    actions=[ft.Button("OK", on_click=lambda e: self.main_page.pop_dialog())],
                    on_dismiss=lambda e: None
                )
            else:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("Try again. Try not to mess up many times or Scratch might flag you as a clanker."),
                    actions=[ft.Button("OK", on_click=lambda e: self.main_page.pop_dialog())],
                    on_dismiss=lambda e: None
                )
            self.main_page.show_dialog(dlg)
        else:
            await self.main_page.push_route("/project-select")

class ProjectSelectScreen(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/project-select")
        self.main_page = page
        self.horizontal_alignment = "center"
        self.vertical_alignment = "center"

        self.output_dir = get_default_download_dir()

        self.title = ft.Text(
            "Projects to Download",
            size=32,
            weight="w600"
        )
        self.project_label = ft.Text("", size=16)
        self.project_optmenu = ft.Dropdown(
            width=220,
            hint_text="Sort by",
            options=[
                ft.DropdownOption(key="all", text="all"),
                ft.DropdownOption(key="shared", text="shared"),
                ft.DropdownOption(key="unshared", text="unshared"),
            ],
            on_select=self.handle_filter_change
        )
        self.project_selectall_button = ft.Button(
            "Select all",
            on_click=self.select_all_projects
        )
        self.project_checklist = ft.ListView(
            spacing=2,
            padding=10,
            width=480, height=300,
            controls=[]
        )

        self.skip_existing_checkbox = ft.Checkbox(
            "Skip already downloaded projects (resume previous unfinished downloads)",
            True
        )
        self.output_dir_label = ft.Text(
            f"Output: {self.output_dir}"
        )
        self.browse_button = ft.Button(
            "Browse...",
            on_click=self.browse_output_dir
        )
        self.filedialog = ft.FilePicker()
        self.download_button = ft.Button(
            "Download selected",
            on_click=self.download_selected_projects,
            disabled=True
        )

        self.controls = [
            self.title,
            self.project_optmenu,
            self.project_selectall_button,
            self.project_checklist,
            self.skip_existing_checkbox,
            self.output_dir_label,
            self.browse_button,
            self.download_button
        ]

    # TODO: write these functions and connect them to controls
    def select_all_projects(self, e):
        for c in self.project_checklist.controls:
            c.value = True
        self.project_selectall_button.on_click = self.deselect_all_projects

    def deselect_all_projects(self, e):
        for c in self.project_checklist.controls:
            c.value = False
        self.project_selectall_button.on_click = self.select_all_projects

    async def browse_output_dir(self, e):
        chosen = await self.filedialog.get_directory_path()
        if chosen:
            self.output_dir = Path(chosen)
            self.output_dir_label.value = f"Output {self.output_dir}"
            self.page.update()

    def get_selected_projects(self):
        '''Returns a list of the indices of checked boxes'''
        selected = []
        for i in range(len(self.project_checklist.controls)):
            checked = self.project_checklist.controls[i].value
            if checked:
                selected.append(i)
        return selected

    async def download_selected_projects(self, e):
        selected = self.get_selected_projects()
        total_projects = len(selected)

        if total_projects == 0:
            dlg = ft.AlertDialog(
                title="Nothing selected",
                content=ft.Text("Please select at least one project."),
                actions=[ft.Button("OK", on_click=lambda e: self.main_page.pop_dialog())],
                on_dismiss=lambda e: None
            )
            self.main_page.show_dialog(dlg)
            return

        step_val = 1.0 / total_projects
        download_args["selected"] = selected
        download_args["total_projects"] = total_projects
        download_args["step_val"] = step_val
        download_args["skip_existing"] = self.skip_existing_checkbox.value
        await self.main_page.push_route("/downloads")

    async def handle_filter_change(self, e):
        self.project_label.value = "Loading projects"
        self.controls.insert(1, self.project_label)
        self.project_optmenu.disabled = True
        self.page.update()
        try:
            filter_arg = e.control.value
            projects = DOWNLOAD_CONTROLLER.get_projects(filter_arg)
            self.download_button.disabled = True
            self.project_label.value = f"Loading projects...{len(projects)} projects found"
            self.page.update()

            self.project_checklist.controls.clear()
            for project in projects:
                cb = ft.Checkbox(label=project.title, value=False)
                self.project_checklist.controls.append(cb)
            await self.project_checklist.scroll_to(offset=0, duration=1000)

            self.download_button.disabled = False
            self.project_optmenu.disabled = False
            self.controls.remove(self.project_label)
            self.page.update()
        except:
            self.project_label.value = "Projects failed to load"
            self.page.update()
            print("boooooooom ")
            # TODO: i love explosions as much as the next guy but we should insert a better error message

class DownloadScreen(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/downloads")
        self.main_page = page
        self.horizontal_alignment = "center"
        self.vertical_alignment = "center"

        self.title = ft.Text(
            "Download in Progress",
            size=32,
            weight="w600"
        )
        # progress bar for current project
        self.cur_download_progress = ft.ProgressBar(
            width=500, height=40
        )
        # progress bar for all projects
        self.all_download_progress = ft.ProgressBar(
            width=500, height=40
        )
        # labels for progress
        self.cur_download_label = ft.Text(
            "Currently downloading [asset title], [num] / [total] assets downloaded"
        )
        self.all_download_label = ft.Text(
            "Currently downloading [project title], [num] / [total] projects downloaded"
        )
        self.back_button = ft.Button(
            content="Back to Projects",
            disabled=True
        )

        self.controls = [
            self.title,
            self.cur_download_progress,
            self.cur_download_label,
            self.all_download_progress,
            self.all_download_label,
            self.back_button
        ]

    def download_selected_projects(self, selected, total_projects, step_val, skip_existing):
        info = DOWNLOAD_CONTROLLER.progress_bar_info
        info["downloaded_projects"] = 0
        info["total_projects"] = total_projects
        info["downloaded_assets"] = 0
        info["total_assets"] = 0
        info["current_project"] = "Starting..."

        self.back_button.disabled = True
        self.all_download_label.value = f"0 / {total_projects} projects downloaded"

        # TODO: actually download the projects and update the progress bars

    def update_progress(self):
        # TODO: update the progress bars with how much has been downloaded
        pass

    def on_downloads_completed(self):
        # TODO: update the text labels and reset the disabled buttons to normal
        pass

async def main(page: ft.Page):
    page.title = "SB3 Bulk Downloader"
    page.window.width = 960
    page.window.height = 720
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    page.route = "/login"

    try: 
        # again this only works for compiled so we dont wanna explode it if it fails in regular python
        page.window.icon = str(ASSETS_DIR / "icon.ico")
    except:
        pass
    
    def route_change(e=None):
        page.views.clear()
        match page.route:
            case "/":
                # TODO: turn into the home screen later
                page.views.append(ft.View(route="/"))
            case "/login":
                page.views.append(LoginScreen(page))
            case "/project-select":
                page.views.append(ProjectSelectScreen(page))
            case "/downloads":
                page.views.append(DownloadScreen(page))
        page.update()

    async def view_pop(e):
        if e.view is not None:
            page.views.remove(e.view)
            top_view = page.views[-1]
            await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    route_change()
    await page.window.center()

ft.run(main)
