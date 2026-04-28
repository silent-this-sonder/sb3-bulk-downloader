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


class LoginScreen(ft.View):
    def __init__(self):
        super().__init__()
        self.horizontal_alignment = "center"
        self.vertical_alignment = "center"

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

    def handle_login(self, e):
        pass

def main(page: ft.Page):
    page.title = "SB3 Bulk Downloader"
    page.window.width = 960
    page.window.height = 720
     
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    dw = app_main.DownloadController()

    page.views.append(LoginScreen())

ft.run(main)
