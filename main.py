import flet as ft
import requests
import boto3
from botocore.exceptions import ClientError

# আপনার API এবং Cognito এর তথ্য
API_URL = "https://6f54fyjspi.execute-api.eu-north-1.amazonaws.com"
CLIENT_ID = "4djq3t8edrf3f513m57cscf727"

# Cognito ক্লায়েন্ট তৈরি (লগইন/সাইনআপের জন্য)
cognito = boto3.client('cognito-idp', region_name='eu-north-1')

def main(page: ft.Page):
    page.title = "Digital Notebook"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 400
    page.window_height = 700

    # ==========================================
    # পেজ ১: লগইন / সাইনআপ স্ক্রিন
    # ==========================================
    def login_screen():
        page.clean()
        
        email = ft.TextField(label="Email", width=300, border_radius=10)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300, border_radius=10)
        
        def show_msg(msg, is_error=True):
            page.snack_bar = ft.SnackBar(ft.Text(msg, color=ft.colors.WHITE), bgcolor=ft.colors.RED if is_error else ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()

        def handle_login(e):
            if not email.value or not password.value:
                show_msg("Please enter email and password!")
                return
            try:
                # Cognito-তে লগইন রিকোয়েস্ট
                response = cognito.initiate_auth(
                    ClientId=CLIENT_ID,
                    AuthFlow='USER_PASSWORD_AUTH',
                    AuthParameters={'USERNAME': email.value, 'PASSWORD': password.value}
                )
                show_msg("Login Successful!", is_error=False)
                # লগইন সফল হলে মেইন পেজে যাবে
                notebook_screen()
            except ClientError as err:
                show_msg(err.response['Error']['Message'])

        def handle_signup(e):
            if not email.value or not password.value:
                show_msg("Please enter email and password!")
                return
            try:
                # Cognito-তে নতুন ইউজার তৈরি
                cognito.sign_up(
                    ClientId=CLIENT_ID,
                    Username=email.value,
                    Password=password.value,
                    UserAttributes=[{'Name': 'email', 'Value': email.value}]
                )
                show_msg("Signup successful! You can now login.", is_error=False)
            except ClientError as err:
                show_msg(err.response['Error']['Message'])

        login_btn = ft.ElevatedButton("Login", on_click=handle_login, width=300, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        signup_btn = ft.TextButton("Create new account", on_click=handle_signup)

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.MENU_BOOK, size=80, color=ft.colors.BLUE_600),
                        ft.Text("Welcome to Notebook", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Login or Sign up to continue", color=ft.colors.GREY_600),
                        ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                        email,
                        password,
                        ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                        login_btn,
                        signup_btn
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=20
            )
        )
        page.update()

    # ==========================================
    # পেজ ২: মেইন নোটবুক স্ক্রিন
    # ==========================================
    def notebook_screen():
        page.clean()
        notes_list = ft.ListView(expand=True, spacing=10, padding=20)

        def load_notes(e=None):
            notes_list.controls.clear()
            try:
                response = requests.get(API_URL)
                if response.status_code == 200:
                    data = response.json()
                    notes = data.get("notes", [])
                    if not notes:
                        notes_list.controls.append(ft.Text("No notes yet. Create one!", italic=True, color=ft.colors.GREY))
                    else:
                        for note in notes:
                            notes_list.controls.append(
                                ft.Container(
                                    content=ft.Text(note.get("text", "Untitled Note")),
                                    padding=15,
                                    border=ft.border.all(1, ft.colors.BLUE_200),
                                    border_radius=10,
                                    bgcolor=ft.colors.BLUE_50
                                )
                            )
                else:
                    notes_list.controls.append(ft.Text(f"Error: {response.status_code}"))
            except Exception as ex:
                notes_list.controls.append(ft.Text(f"Connection Error: {ex}"))
            page.update()

        def save_note(e):
            if not note_input.value:
                return
            payload = {"text": note_input.value}
            try:
                response = requests.post(API_URL, json=payload)
                if response.status_code == 201:
                    note_input.value = ""
                    load_notes()
            except Exception as ex:
                print(f"Error: {ex}")

        def logout(e):
            login_screen()

        note_input = ft.TextField(
            hint_text="Write your note here...",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            border_color=ft.colors.BLUE_400,
            border_radius=10
        )

        save_btn = ft.ElevatedButton("Save Note", on_click=save_note, icon=ft.icons.SAVE, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE))

        header = ft.Row(
            [
                ft.Text("My Digital Notebook", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.icons.LOGOUT, on_click=logout, tooltip="Logout")
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        page.add(
            ft.Container(
                content=ft.Column([
                    header,
                    ft.Divider(),
                    note_input,
                    ft.Row([save_btn], alignment=ft.MainAxisAlignment.END),
                    ft.Divider(),
                    ft.Text("Saved Notes:", size=18, weight=ft.FontWeight.BOLD),
                    notes_list
                ]),
                padding=20,
                expand=True
            )
        )
        load_notes()

    # অ্যাপ চালু হলে প্রথমে লগইন স্ক্রিন দেখাবে
    login_screen()

ft.app(target=main)
