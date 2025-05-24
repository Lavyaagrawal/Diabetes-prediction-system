import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import ObjectProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock
from diabetes_chatbot import OpenRouterChatbot
import re
import requests
import json
import threading
import time

# Fix for window size
Window.size = (360, 640)

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


class WelcomeScreen(Screen):
    terms_accepted = False

    def on_checkbox_active(self, checkbox, value):
        self.terms_accepted = value
        # Update the button state based on checkbox
        if hasattr(self.ids, 'get_started_btn'):
            self.ids.get_started_btn.disabled = not value

    def go_to_terms(self):
        self.manager.transition.direction = 'left'
        self.manager.current = 'terms'

    def go_to_login(self):
        if self.terms_accepted:
            self.manager.transition.direction = 'left'
            self.manager.current = 'login'
        else:
            self.show_terms_required_dialog()

    def show_terms_required_dialog(self):
        dialog = MDDialog(
            title="Terms & Conditions",
            text="Please accept the Terms and Conditions to continue.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class TermsAndConditionsScreen(Screen):
    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = 'welcome'
        welcome_screen = self.manager.get_screen('welcome')

        # Update terms accepted flag
        welcome_screen.terms_accepted = True

        # Find and update checkbox directly in the widget tree
        # This assumes the checkbox is in a BoxLayout that contains a MDTextButton
        for layout in welcome_screen.walk(restrict=True):
            if hasattr(layout, 'children'):
                for child in layout.children:
                    if hasattr(child, 'active') and hasattr(child, 'on_active'):
                        child.active = True
                        # Manually trigger the callback
                        welcome_screen.on_checkbox_active(child, True)
                        break

        # Enable the button
        if hasattr(welcome_screen.ids, 'get_started_btn'):
            welcome_screen.ids.get_started_btn.disabled = False


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


class HomeScreen(Screen):
    user_email = StringProperty("")
    user_fullname = StringProperty("")

    def on_enter(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'current_user') and app.current_user:
            user_info = user_store.get(app.current_user)
            self.user_email = app.current_user
            self.user_fullname = user_info.get('fullname', '')
            firstname = self.user_fullname.split()[0] if self.user_fullname else ""
            if hasattr(self.ids, 'welcome_label'):
                self.ids.welcome_label.text = f"Welcome, {firstname}"

    def logout(self):
        app = MDApp.get_running_app()
        app.current_user = None
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'

    def open_chatbot(self):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'chatbot'

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


class N8nAIChatbot:
    """Integration with n8n AI agent chatbot"""

    def __init__(self, webhook_url=None):
        # Replace with your actual n8n webhook URL
        self.webhook_url = webhook_url or "https://your-actual-n8n-domain/webhook/ai-chat"
        self.session_id = f"session_{int(time.time())}"
        self.conversation_history = []

        # Add internet connection check
        self.has_internet = self.check_internet_connection()

    def check_internet_connection(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def generate_response(self, user_message):
        if not self.has_internet:
            return self.get_fallback_response(user_message)
        try:
            # Add message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Prepare the payload for n8n
            payload = {
                "session_id": self.session_id,
                "message": user_message,
                "conversation_history": self.conversation_history
            }

            # Send request to n8n webhook
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                # Process successful response
                try:
                    result = response.json()
                    ai_response = result.get("response", "Sorry, I couldn't process that request. Please try again.")

                    # Add AI response to conversation history
                    self.conversation_history.append({"role": "assistant", "content": ai_response})

                    return ai_response
                except json.JSONDecodeError:
                    return "Received an invalid response from the AI service. Please try again later."
            else:
                return f"Sorry, I'm having trouble connecting to my knowledge base. (Status code: {response.status_code})"

        except requests.exceptions.Timeout:
            return "The AI service is taking too long to respond. Please try again later."
        except requests.exceptions.ConnectionError:
            return "Unable to connect to the AI service. Please check your internet connection."
        except Exception as e:
            print(f"Error connecting to n8n AI agent: {str(e)}")
            return "I'm having technical difficulties. Please try again in a moment."

    # Fallback response in case n8n service is unavailable
    def get_fallback_response(self, message):
        message = message.lower()
        if any(word in message for word in ["hello", "hi", "hey"]):
            return "Hello! How can I assist you with diabetes information today?"
        elif "symptom" in message:
            return "Common diabetes symptoms include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, and blurred vision. I recommend consulting with a healthcare professional about any symptoms."
        elif "diet" in message:
            return "A balanced diet for diabetes management typically includes plenty of vegetables, whole grains, lean proteins, and healthy fats. It's important to limit refined carbs and added sugars."
        elif "exercise" in message:
            return "Regular physical activity is important for managing diabetes. Aim for at least 150 minutes of moderate exercise per week, spread over at least 3 days."
        else:
            return "I can provide information about diabetes management, including diet, exercise, symptoms, and treatments. How can I help you today?"


class ChatbotScreen(Screen):
    chat_history = StringProperty("")
    chatbot = None
    is_sending = False
    suggestions = []

    def on_enter(self):
        """Initialize the screen when it becomes active"""
        # Initialize chatbot if needed
        self.initialize_chatbot()

        # Set welcome message if chat is empty
        if not self.chat_history:
            app = MDApp.get_running_app()
            firstname = "there"
            if hasattr(app, 'current_user') and app.current_user:
                try:
                    user_info = user_store.get(app.current_user)
                    firstname = user_info.get('fullname', '').split()[0] if user_info.get('fullname') else "there"
                except KeyError:
                    pass

            # Welcome message with emoji
            self.chat_history = f"Chatbot: 👋 Hello {firstname}! I'm your diabetes health assistant powered by Ollama AI. How can I help you today?"

            # Update suggestion buttons
            Clock.schedule_once(lambda dt: self.update_suggestions(), 0.5)

            # Scroll to bottom
            Clock.schedule_once(lambda dt: setattr(self.ids.chat_scroll, 'scroll_y', 0), 0.1)

    def initialize_chatbot(self):
        """Initialize the chatbot instance"""
        if not self.chatbot:
            # Create a new chatbot instance with OpenRouter
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                print("Warning: OPENROUTER_API_KEY environment variable not set")
                return
                
            self.chatbot = OpenRouterChatbot(
                api_key=api_key,
                model="anthropic/claude-3-opus",
                debug=True
            )

            # Set username if available
            app = MDApp.get_running_app()
            if hasattr(app, 'current_user') and app.current_user:
                try:
                    user_info = user_store.get(app.current_user)
                    self.chatbot.set_username(user_info.get('fullname', app.current_user))
                except KeyError:
                    pass

    def update_suggestions(self):
        """Update the suggestion buttons"""
        if not self.chatbot:
            return

        # Get new suggestions
        self.suggestions = self.chatbot.get_suggested_queries(3)

        # Clear existing suggestions
        if hasattr(self.ids, 'suggestion_container'):
            self.ids.suggestion_container.clear_widgets()

            # Add new suggestion buttons with improved styling
            for suggestion in self.suggestions:
                btn = MDFlatButton(
                    text=suggestion,
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color if hasattr(self, 'theme_cls') else [0.2, 0.6, 0.6, 1],
                    line_color=self.theme_cls.primary_color if hasattr(self, 'theme_cls') else [0.2, 0.6, 0.6, 1],
                    on_release=lambda x, q=suggestion: self.use_suggestion(q)
                )
                self.ids.suggestion_container.add_widget(btn)

    def use_suggestion(self, suggestion_text):
        """Use a suggested query"""
        self.ids.message_input.text = suggestion_text
        self.send_message()

    def send_message(self):
        """Send the user's message to the chatbot"""
        # Prevent multiple sends at once
        if self.is_sending:
            return

        user_message = self.ids.message_input.text.strip()
        if not user_message:
            return

        # Add user message to chat history with emoji
        self.chat_history += f"\n\n💬 You: {user_message}"
        self.ids.message_input.text = ""

        # Show typing indicator with animation
        typing_indicator = "\n\n🤖 Assistant: [i]Thinking...[/i]"
        self.chat_history += typing_indicator

        # Scroll to bottom to show typing indicator
        Clock.schedule_once(lambda dt: setattr(self.ids.chat_scroll, 'scroll_y', 0))

        # Process message in background thread
        self.is_sending = True
        threading.Thread(
            target=self._get_response,
            args=(user_message, typing_indicator),
            daemon=True
        ).start()

    def _get_response(self, user_message, typing_indicator):
        """Get response from chatbot in background thread"""
        try:
            # Ensure chatbot is initialized
            if not self.chatbot:
                self.initialize_chatbot()

            # Get response from chatbot
            response = self.chatbot.generate_response(user_message)

            # Update UI in main thread
            Clock.schedule_once(
                lambda dt: self._update_chat_with_response(typing_indicator, response),
                0
            )

            # Update suggestions after response
            Clock.schedule_once(
                lambda dt: self.update_suggestions(),
                0.5
            )
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            error_msg = "Sorry, I'm having technical difficulties. Please try again."
            Clock.schedule_once(
                lambda dt: self._update_chat_with_response(typing_indicator, error_msg),
                0
            )
        finally:
            # Reset sending flag
            Clock.schedule_once(lambda dt: setattr(self, 'is_sending', False), 0)

    def _update_chat_with_response(self, typing_indicator, response):
        """Update chat with bot response"""
        # Replace typing indicator with actual response
        self.chat_history = self.chat_history.replace(
            typing_indicator,
            f"\n\n🤖 Assistant: {response}"
        )

        # Scroll to bottom
        Clock.schedule_once(lambda dt: setattr(self.ids.chat_scroll, 'scroll_y', 0))

    def clear_chat(self):
        """Clear the chat history"""
        if self.chatbot:
            self.chatbot.clear_conversation()

        # Set new welcome message with emoji
        app = MDApp.get_running_app()
        firstname = "there"
        if hasattr(app, 'current_user') and app.current_user:
            try:
                user_info = user_store.get(app.current_user)
                firstname = user_info.get('fullname', '').split()[0] if user_info.get('fullname') else "there"
            except KeyError:
                pass

        self.chat_history = f"Chatbot: 👋 Hello {firstname}! I'm your diabetes health assistant powered by Ollama AI. How can I help you today?"

        # Update suggestions
        self.update_suggestions()

        # Scroll to top
        Clock.schedule_once(lambda dt: setattr(self.ids.chat_scroll, 'scroll_y', 1))

    def go_back(self):
        """Return to home screen"""
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'home'


class DiabetesApp(MDApp):
    current_user = None

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "BlueGray"
        self.theme_cls.theme_style = "Light"

        Builder.load_file('healthcare.kv')

        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(TermsAndConditionsScreen(name='terms'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SignupScreen(name='signup'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ChatbotScreen(name='chatbot'))

        return sm


if __name__ == '__main__':
    DiabetesApp().run()