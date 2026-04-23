import flet as ft
import sys
from pathlib import Path
import main as app_main


BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS_DIR = BASE_DIR / "assets"


def main(page: ft.Page):
    page.title = "SB3 Bulk Downloader"
    page.window.width = 960
    page.window.height = 720
     
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"


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

    sb_text = ft.Text("SB3 Bulk Downloader", size=32, weight="w600")
    disclaimer  = ft.Text("Credentials are only sent to Scratch's servers, and we don't store them.", size=12, color="grey600")

    username_field = ft.TextField(label="Username", hint_text="Enter a Scratch username")
    password_field = ft.TextField(label="Password", hint_text="Enter your password", password=True, can_reveal_password=True)
    login = ft.Button(
        content="Sign in",
        on_click=lambda _: app_main.validate_login(username_field.value, password_field.value),
        color="white",
        
        bgcolor="#855cd6"
    )
    page.add(sb_text, logo_image, disclaimer, username_field, password_field, login)


    page.update()

if __name__ == "__main__":
    ft.run(main)
