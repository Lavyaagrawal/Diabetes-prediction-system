import os
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
import re

# Setup user data directory
user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data')
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)
user_store = JsonStore(os.path.join(user_data_dir, 'users.json'))

class SecurityQuestionDialog(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = [
            "What was your childhood nickname?",
            "What is the name of your first pet?",
            "What is your mother's maiden name?",
            "In what city were you born?",
            "What high school did you attend?"
        ]

    def open_questions_menu(self):
        menu_items = [
            {
                "text": question,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=question: self.set_question(x),
            } for question in self.questions
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.security_question,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def set_question(self, question_text):
        self.ids.security_question.text = question_text
        self.menu.dismiss()

class ForgotPasswordDialog(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.email.text = ""
        self.ids.security_answer.text = ""

class ResetPasswordContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "12dp"
        self.size_hint_y = None
        self.height = "100dp"
        self.padding = [20, 0, 20, 0]

        self.password_field = MDTextField(
            hint_text="New Password",
            helper_text="Minimum 6 characters",
            helper_text_mode="on_focus",
            icon_right="lock",
            password=True,
            required=True
        )

        self.add_widget(self.password_field)

class LoginScreen(Screen):
    email = ObjectProperty(None)
    password = ObjectProperty(None)
    forgot_password_dialog = None
    reset_password_dialog = None

    def validate_user(self):
        email = self.email.text.strip()
        password = self.password.text.strip()

        if not email or not password:
            self.show_dialog("Error", "Please fill in all fields.")
            return

        if not self.validate_email(email):
            self.show_dialog("Error", "Please enter a valid email address.")
            return

        if email in user_store:
            stored_user = user_store.get(email)
            if stored_user['password'] == password:
                app = MDApp.get_running_app()
                app.current_user = email
                self.reset_form()
                self.manager.transition.direction = 'left'
                self.manager.current = 'home'
            else:
                self.show_dialog("Login Failed", "Incorrect password. Please try again.")
        else:
            self.show_dialog("Login Failed", "Email not registered. Please sign up.")

    def validate_email(self, email):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email)

    def reset_form(self):
        self.email.text = ""
        self.password.text = ""

    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_forgot_password_dialog(self):
        if self.forgot_password_dialog:
            self.forgot_password_dialog.dismiss()
            self.forgot_password_dialog = None

        self.forgot_password_dialog = MDDialog(
            title="Forgot Password",
            type="custom",
            content_cls=ForgotPasswordDialog(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.forgot_password_dialog.dismiss()
                ),
                MDFlatButton(
                    text="VERIFY",
                    on_release=self.verify_security_question
                )
            ]
        )
        self.forgot_password_dialog.open()

    def verify_security_question(self, instance):
        if not self.forgot_password_dialog:
            return

        content = self.forgot_password_dialog.content_cls
        email = content.ids.email.text.strip()
        answer = content.ids.security_answer.text.strip()

        if not email or not answer:
            self.show_dialog("Error", "Please fill in all fields.")
            return

        if email in user_store:
            user_data = user_store.get(email)
            if user_data.get('security_answer', '').lower() == answer.lower():
                self.forgot_password_dialog.dismiss()
                self.show_reset_password_dialog(email)
            else:
                self.show_dialog("Error", "Incorrect security answer.")
        else:
            self.show_dialog("Error", "Email not found.")

    def show_reset_password_dialog(self, email):
        if self.reset_password_dialog:
            self.reset_password_dialog.dismiss()
            self.reset_password_dialog = None

        content = ResetPasswordContent()
        self.reset_password_dialog = MDDialog(
            title="Reset Password",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.reset_password_dialog.dismiss()
                ),
                MDFlatButton(
                    text="RESET",
                    on_release=lambda x: self.reset_password(email)
                )
            ]
        )
        self.reset_password_dialog.open()

    def reset_password(self, email, *args):
        if not self.reset_password_dialog:
            return

        content = self.reset_password_dialog.content_cls
        new_password = content.password_field.text

        if len(new_password) < 6:
            self.show_dialog("Error", "Password must be at least 6 characters long.")
            return

        user_data = user_store.get(email)
        user_data['password'] = new_password
        user_store.put(email, **user_data)

        self.reset_password_dialog.dismiss()
        self.reset_password_dialog = None
        self.show_dialog("Success", "Password has been reset successfully.")

class SignupScreen(Screen):
    fullname = ObjectProperty(None)
    email = ObjectProperty(None)
    password = ObjectProperty(None)
    confirm_password = ObjectProperty(None)
    sec_dialog = None

    def register_user(self):
        fullname = self.fullname.text.strip()
        email = self.email.text.strip()
        password = self.password.text.strip()
        confirm_password = self.confirm_password.text.strip()

        if not fullname or not email or not password or not confirm_password:
            self.show_dialog("Error", "Please fill in all fields.")
            return

        if not self.validate_email(email):
            self.show_dialog("Error", "Please enter a valid email address.")
            return

        if password != confirm_password:
            self.show_dialog("Error", "Passwords do not match.")
            return

        if len(password) < 6:
            self.show_dialog("Error", "Password must be at least 6 characters long.")
            return

        if email in user_store:
            self.show_dialog("Registration Failed", "Email already registered. Please login.")
            return

        self.show_security_question_dialog(fullname, email, password)

    def validate_email(self, email):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email)

    def reset_form(self):
        self.fullname.text = ""
        self.email.text = ""
        self.password.text = ""
        self.confirm_password.text = ""

    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_security_question_dialog(self, fullname, email, password):
        if self.sec_dialog:
            self.sec_dialog.dismiss()
            self.sec_dialog = None

        self.sec_dialog = MDDialog(
            title="Security Question",
            type="custom",
            content_cls=SecurityQuestionDialog(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.sec_dialog.dismiss()
                ),
                MDFlatButton(
                    text="SAVE",
                    on_release=lambda x: self.complete_registration(fullname, email, password, x)
                )
            ]
        )
        self.sec_dialog.open()

    def complete_registration(self, fullname, email, password, instance):
        if not self.sec_dialog:
            return

        content = self.sec_dialog.content_cls
        security_question = content.ids.security_question.text
        security_answer = content.ids.security_answer.text.strip()

        if not security_question or security_question == "Select a security question" or not security_answer:
            self.show_dialog("Error", "Please select a security question and provide an answer.")
            return

        user_store.put(email, fullname=fullname, password=password,
                       security_question=security_question, security_answer=security_answer)

        self.sec_dialog.dismiss()
        self.sec_dialog = None
        self.show_dialog("Success", "Registration successful! Please login.")
        self.reset_form()
        self.manager.transition.direction = 'right'
        self.manager.current = 'login' 