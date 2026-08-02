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

class LoginScreen(ft.View):
    def __init__(self, page: ft.Page, dw: app_main.DownloadController):
        # TODO: connect to logic
        super().__init__(route="/login")
        self.dw = dw
        self.main_page = page
        self.horizontal_alignment = "center"
        self.vertical_alignment = "center"

        self.fail_counter = 0
        self.empty_counter = 0

        self.logo_image = ft.Image(
            src=str(ASSETS_DIR / "icon.png"),
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

        success = self.dw.validate_login(self.username_field.value, self.password_field.value)
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
    def __init__(self, page: ft.Page, dw: app_main.DownloadController):
        super().__init__(route="/project-select")
        self.dw = dw
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
        self.project_selectall_button = ft.Button("Select all")
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
        self.browse_button = ft.Button("Browse...")
        self.download_button = ft.Button("Download selected", disabled=True)

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

    def handle_filter_change(self, e):
        self.project_label.value = "Loading projects"
        self.controls.insert(1, self.project_label)
        self.project_optmenu.disabled = True
        self.page.update()
        try:
            filter_arg = e.control.value
            projects = self.dw.get_projects(filter_arg)
            self.project_label.value = f"Loading projects...{len(projects)} projects found"
            self.page.update()

            self.project_checklist.controls.clear()
            for project in projects:
                cb = ft.Checkbox(label=project.title, value=False)
                self.project_checklist.controls.append(cb)

            self.project_optmenu.disabled = False
            self.controls.remove(self.project_label)
            self.page.update()
        except:
            self.project_label.value = "Projects failed to load"
            self.page.update()
            print("boooooooom ")
            # TODO: i love explosions as much as the next guy but we should insert a better error message

class DownloadScreen(ft.View):
    def __init__(self, page: ft.Page, dw: app_main.DownloadController):
        super().__init__(route="/downloads")
        self.dw = dw
        self.main_page = page
        self.horizontal_alignment = "center"
        self.vertical_alignment = "center"
        self.controls = [
        ]

def main(page: ft.Page):
    page.title = "SB3 Bulk Downloader"
    page.window.width = 960
    page.window.height = 720
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    page.route = "/login"

    dw = app_main.DownloadController()

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
                page.views.append(LoginScreen(page, dw))
            case "/project-select":
                page.views.append(ProjectSelectScreen(page, dw))
            case "/downloads":
                page.views.append(DownloadScreen(page, dw))
        page.update()

    async def view_pop(e):
        if e.view is not None:
            page.views.remove(e.view)
            top_view = page.views[-1]
            await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    route_change()

ft.run(main)
