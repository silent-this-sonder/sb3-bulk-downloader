from pathlib import Path
import sys
import threading

import flet as ft

import main as app_main


def get_default_download_dir() -> Path:
    downloads = Path.home() / "Downloads"
    base_dir = downloads if downloads.exists() else Path.home()
    return base_dir / "Scratch-Projects"

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS_DIR = BASE_DIR / "assets"


def main(page: ft.Page):
    page.title = "SB3 Bulk Downloader"
    page.window.width = 960
    page.window.height = 720
     
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    dw = app_main.DownloadController()

    logo_image = ft.Image(
        src=str(ASSETS_DIR / "logo.png"),
        width=200,
        height=200,
        fit="contain",
    )
    try: 
         # again this only works for compiled so we dont wanna explode it if it fails in regular python
        page.window.icon = str(ASSETS_DIR / "icon.ico")
    except:
        pass

    sb_text = ft.Text("Scratch Project Bulk Downloader", size=32, weight="w600")
    disclaimer  = ft.Text("Credentials are only sent to Scratch's servers, and we don't store them.", size=12, color="grey600")
    
    fail_counter = 0
    empty_counter = 0
    # just for the funsies
    with open(ASSETS_DIR / "login_messages.txt", "r", encoding="utf-8") as f:
        login_messages = f.readlines()

    def handle_login(e):
        nonlocal fail_counter
        nonlocal empty_counter

        # check if someone made it empty so it doesn't keep sending fail requests to scratch and get flagged or smth
        if empty_counter < len(login_messages) and (not username_field.value or not password_field.value):
            dlg = ft.AlertDialog(
                title="Login Failed",
                content=ft.Text(login_messages[empty_counter]),
                actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                on_dismiss=lambda e: None
            )
            page.show_dialog(dlg)
            empty_counter += 1
            return

        success = dw.validate_login(username_field.value, password_field.value)
        if not success:
            fail_counter += 1
            if fail_counter >= 4:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("Are you guessing passwords or something? Please type valid Scratch Account credentials. If you keep messing up, your IP might get banned by Scratch."),
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                    on_dismiss=lambda e: None

                )
                

            else:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("Try again. Try not to mess up many times or Scratch might flag you as a clanker."),
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                    on_dismiss=lambda e: None

                )
            page.show_dialog(dlg)
        else:
            ProjectSelectScreen()

    login = ft.Button(
        content="Sign in",
        on_click=handle_login,
        color="white",
        bgcolor="#855cd6"
    )

    username_field = ft.TextField(label="Username", hint_text="Enter a Scratch username", on_submit=handle_login)
    password_field = ft.TextField(label="Password", hint_text="Enter your password", password=True, can_reveal_password=True, on_submit=handle_login)
    def login_screen(): # TODO: should we refactor this into a class later like the original?
        page.clean()
        page.add(sb_text, logo_image, disclaimer, username_field, password_field, login)



        page.update()
    login_screen()
 

    def ProjectSelectScreen():
        page.clean()
        project_opts = ["all", "shared", "unshared"]
        project_label = ft.Text("Projects to Download", size=32, weight="w600")
        # for some reason flet doesn't let me set the same color for the hint text than the actual thing so i have to do it separately
        hintstyle= ft.TextStyle(color="white")
        project_optmenu = ft.Dropdown(
            options=[ft.dropdown.Option(key=opt, text=opt.capitalize()) for opt in project_opts],


        

         hint_text="Sort by", bgcolor="#855cd6",color="white" , fill_color="#855cd6", filled=True, hint_style=hintstyle, on_text_change=lambda e: None) # TODO: format atrocious indenting
        def handle_filter_change(e):
            project_label.value = "loading Projects..."
            project_optmenu.disabled = True
            page.update()
            try:
                filter_arg = e.control.value
                projects = dw.get_projects(filter_arg)
                project_checklist.controls.clear()
                for project in projects:
                    cb = ft.Checkbox(label=project.title, value=False)
                    project_checklist.controls.append(cb)
            except:
                print("boooooooom ")
        project_checklist = ft.Column(height=300)
        
        
        page.add(
        project_label,
        project_optmenu,
        ft.Column([
            ft.Checkbox(label="Buy groceries", value=False),
            ft.Checkbox(label="Walk the dog", value=True),
            ft.Checkbox(label="Finish Flet project", value=False),
        ])
    )
        page.update()
        


if __name__ == "__main__":
    ft.run(main)
