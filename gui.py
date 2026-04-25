import flet as ft
import sys
from pathlib import Path
import main as app_main
import threading


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

    sb_text = ft.Text("SB3 Bulk Downloader", size=32, weight="w600")
    disclaimer  = ft.Text("Credentials are only sent to Scratch's servers, and we don't store them.", size=12, color="grey600")
    
    fail_counter = 0
    empty_counter = 0

    def handle_login(e):
        nonlocal fail_counter
        nonlocal empty_counter
        # just for the funsies
        
        # check if someone made it empty so it doesn't keep sending fail requests to scratch and get flagged or smth

        if not username_field.value or not password_field.value:
            empty_counter += 1
            if empty_counter >= 3 and empty_counter < 6:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("WHY DO YOU KEEP LEAVING THE FIELDS EMPTY?!?!!? "), # TODO: @silent-this-sonder you might wanna make this funnier or softer idk
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                    on_dismiss=lambda e: None

                )
                page.show_dialog(dlg)
            elif empty_counter >= 6 and empty_counter < 9:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("WHAT ARE YOU DOING? DID YOU FALL ASLEEP ON THE LOGIN BUTTON?!? STOP!!!11!"),
                    on_dismiss=lambda e: None

                )
                page.show_dialog(dlg)

            elif empty_counter >= 9 and empty_counter < 20:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("ARE YOU OK? DO YOU NEED HELP? ARE YOU JUST SPAMMING THE LOGIN BUTTON FOR FUN? This is definitely getting me to Scratch my head."),
                    on_dismiss=lambda e: None

                )
                page.show_dialog(dlg)
            elif empty_counter >= 20 and empty_counter <= 30:
                    dlg = ft.AlertDialog(
                        title="Login Failed",
                        content=ft.Text("You need help."),
                        on_dismiss=lambda e: None
    
                    )
                    page.show_dialog(dlg)
            elif empty_counter > 30 and empty_counter <= 100:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("STOP IT."),
                    on_dismiss=lambda e: None
    
                )
                page.show_dialog(dlg)
            elif empty_counter > 100:
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("Think about all the time you just spent spamming this button for absolutely no reason expecting it to get increasingly angrier. That's it. You've done it. There are no more increasingly angrier messages. This is the last one. Think about all the time you just wasted. You could've been playing games, doing work, something productive. No, instead you chose to waste your precious, limited time in clicking a login button. You can't time travel backwards. You can't regain the time you lost doing this. You only kept being persistent for that quick and easy dopamine hit of getting an increasingly funnier message. Is that how your whole life works? You waste time because it's funny? Because it's entertaining? Because maybe you should rethink what you could've been doing this whole time................................ Anyways, how are you liking this tool? Don't forget to star the repo and give us a nice message in the forum topic!"),
                    on_dismiss= lambda e: sys.exit(67)
                    
                )
                page.show_dialog(dlg)
            else: 
                dlg = ft.AlertDialog(
                    title="Login Failed",
                    content=ft.Text("Please type something in both fields."),
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                    on_dismiss=lambda e: None

                )
                page.show_dialog(dlg)
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

    placeholder = ft.Text("placeholder for project select screen", size=67, color="red")

    def ProjectSelectScreen():
        page.clean()
        page.add(placeholder)
        page.update()
        


if __name__ == "__main__":
    ft.run(main)
