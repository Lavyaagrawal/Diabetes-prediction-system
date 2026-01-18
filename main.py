import os
import sys

# PyInstaller compatibility: get resource path
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

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

import joblib
import pickle
import numpy as np

# Fix for window size
Window.size = (360, 640)

# Setup user data directory (use executable directory, not temp)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

user_data_dir = os.path.join(application_path, 'user_data')
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
            
        # Schedule transition to login page after 2 seconds when checkbox is checked
        if value:
            Clock.schedule_once(lambda dt: self.go_to_login(), 2)

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
    current_glucose = StringProperty("--")
    last_reading_time = StringProperty("No recent readings")
    
    def on_enter(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'current_user') and app.current_user:
            user_info = user_store.get(app.current_user)
            self.user_email = app.current_user
            self.user_fullname = user_info.get('fullname', '')
            firstname = self.user_fullname.split()[0] if self.user_fullname else ""
            if hasattr(self.ids, 'welcome_label'):
                self.ids.welcome_label.text = f"Hi, {firstname}!"
            
            # Load user's health data if available
            if 'health_data' in user_info:
                health_data = user_info['health_data']
                self.current_glucose = health_data.get('last_glucose', '--')
                self.last_reading_time = health_data.get('last_reading_time', 'No recent readings')

    def logout(self):
        app = MDApp.get_running_app()
        app.current_user = None
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'

    def open_chatbot(self):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'chatbot'

    def add_reading(self):
        self.show_dialog("Add Reading", "This feature will be available soon!")

    def view_insights(self):
        self.show_dialog("Health Insights", "Detailed health insights will be available soon!")

    def open_reminders(self):
        self.show_dialog("Reminders", "Medication and reading reminders will be available soon!")

    def open_reports(self):
        self.show_dialog("Reports", "Detailed health reports will be available soon!")

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

    def start_symptom_assessment(self):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'symptom_assessment'


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


class SymptomAssessmentScreen(Screen):
    def go_home(self, *args):
        self.manager.transition.direction = 'right'
        self.manager.current = 'home'

    def predict(self):
        try:
            # Collect input values
            vals = {
                'Pregnancies': float(self.ids.pregnancies.text.strip()),
                'Glucose': float(self.ids.glucose.text.strip()),
                'Blood Pressure': float(self.ids.blood_pressure.text.strip()),
                'Skin Thickness': float(self.ids.skin_thickness.text.strip()),
                'Insulin': float(self.ids.insulin.text.strip()),
                'BMI': float(self.ids.bmi.text.strip()),
                'Diabetes Pedigree Function': float(self.ids.diabetes_pedigree.text.strip()),
                'Age': float(self.ids.age.text.strip())
            }

            # Format prompt for OpenRouter AI
            prompt = (
                "You are a diabetes risk prediction model. Given the following patient data, output ONLY whether the patient is 'Diabetic' or 'Not Diabetic' (and optionally a probability/confidence score). "
                "Do NOT mention that you are an AI or language model. Here is the data:\n" +
                "\n".join([f"{k}: {v}" for k, v in vals.items()]) +
                "\nOutput format:\nPrediction: <Diabetic/Not Diabetic>\nProbability: <number between 0 and 1> (optional)"
            )

            # Initialize chatbot if needed
            if not hasattr(self, 'chatbot'):
                api_key = "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"
                self.chatbot = OpenRouterChatbot(
                    api_key=api_key,
                    model="anthropic/claude-3-opus",
                    debug=True
                )

            # Show loading dialog
            self.show_dialog("Please wait", "Analyzing your health data...")

            def get_response():
                try:
                    response = self.chatbot.generate_response(prompt)
                except Exception as e:
                    print(f"Error in prediction: {str(e)}")
                    # Generate fallback response based on input values
                    glucose = float(vals['Glucose'])
                    bmi = float(vals['BMI'])
                    age = float(vals['Age'])
                    
                    # Simple heuristic for fallback prediction
                    risk_factors = 0
                    if glucose > 140: risk_factors += 1
                    if bmi > 30: risk_factors += 1
                    if age > 50: risk_factors += 1
                    
                    is_diabetic = risk_factors >= 2
                    confidence = 0.5 + (risk_factors * 0.1)  # Base confidence + adjustment
                    
                    response = f"Prediction: {'Diabetic' if is_diabetic else 'Not Diabetic'}\nProbability: {confidence:.2f}"
                
                Clock.schedule_once(lambda dt: self.show_prediction_result(response), 0)

            import threading
            threading.Thread(target=get_response, daemon=True).start()

        except ValueError:
            self.show_dialog("Input Error", "Please fill all fields with valid numbers.")
        except Exception as e:
            print(f"Error: {str(e)}")
            self.show_dialog("Error", "An error occurred during prediction. Please try again.")

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

    def show_prediction_result(self, result):
        """Handle and display the prediction result with graceful error handling"""
        try:
            # Handle potential malformed responses
            lines = result.strip().split('\n') if result else []
            
            # Default values
            prediction = None
            probability = None
            
            # Try to parse prediction and probability from result
            for line in lines:
                if 'Prediction:' in line:
                    pred = line.split('Prediction:')[1].strip()
                    if pred and pred != "Unknown":
                        prediction = pred
                elif 'Probability:' in line:
                    try:
                        prob = float(line.split('Probability:')[1].strip())
                        if 0 <= prob <= 1:
                            probability = prob
                    except (ValueError, IndexError):
                        pass

            # If no valid prediction was found, determine based on risk factors
            if not prediction or not probability:
                try:
                    # Get the input values
                    glucose = float(self.ids.glucose.text.strip())
                    bmi = float(self.ids.bmi.text.strip())
                    age = float(self.ids.age.text.strip())
                    insulin = float(self.ids.insulin.text.strip())
                    blood_pressure = float(self.ids.blood_pressure.text.strip())
                    
                    # Calculate risk score
                    risk_score = 0
                    if glucose > 140: risk_score += 2
                    elif glucose > 125: risk_score += 1
                    
                    if bmi > 30: risk_score += 2
                    elif bmi > 25: risk_score += 1
                    
                    if age > 45: risk_score += 1
                    if insulin > 140: risk_score += 1
                    if blood_pressure > 140: risk_score += 1
                    
                    # Determine prediction and probability based on risk score
                    max_risk_score = 7
                    probability = min(0.95, risk_score / max_risk_score)
                    prediction = "Diabetic" if probability > 0.5 else "Not Diabetic"
                    
                except Exception:
                    # If calculation fails, use moderate risk as fallback
                    prediction = "Not Diabetic"
                    probability = 0.45

            # Generate risk level and recommendation
            if probability > 0.7:
                risk_level = "High Risk"
                recommendation = "Immediate medical consultation is strongly recommended"
            elif probability > 0.5:
                risk_level = "Moderate to High Risk"
                recommendation = "Schedule a check-up with your healthcare provider soon"
            elif probability > 0.3:
                risk_level = "Moderate Risk"
                recommendation = "Regular monitoring and lifestyle modifications advised"
            else:
                risk_level = "Low Risk"
                recommendation = "Maintain a healthy lifestyle and regular check-ups"

            # Format the detailed result
            detailed_result = (
                f"Prediction: {prediction}\n\n"
                f"Risk Assessment:\n"
                f"- Risk Level: {risk_level}\n"
                f"- Confidence Score: {probability:.0%}\n\n"
                f"Recommendation:\n{recommendation}\n\n"
                "Note: This is an AI-assisted prediction and should not replace professional medical advice. "
                "Please consult with a healthcare provider for accurate diagnosis and treatment."
            )

            self.show_dialog("Prediction Result", detailed_result)
            
        except Exception as e:
            print(f"Error formatting prediction result: {str(e)}")
            # Provide a graceful fallback response with a clear prediction
            fallback_result = (
                "Prediction: Not Diabetic\n\n"
                "Risk Assessment:\n"
                "- Risk Level: Moderate Risk\n"
                "- Confidence Score: 45%\n\n"
                "Recommendation:\n"
                "Due to technical limitations, we're showing a conservative estimate. "
                "Please consult with a healthcare professional for an accurate assessment.\n\n"
                "Note: This fallback prediction should not replace professional medical advice."
            )
            self.show_dialog("Prediction Result", fallback_result)


class DiabetesApp(MDApp):
    current_user = None

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "BlueGray"
        self.theme_cls.theme_style = "Light"

        # Load KV file with proper resource path
        kv_file = resource_path('diabetes_app.kv')
        Builder.load_file(kv_file)

        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(TermsAndConditionsScreen(name='terms'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(SignupScreen(name='signup'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ChatbotScreen(name='chatbot'))
        sm.add_widget(SymptomAssessmentScreen(name='symptom_assessment'))

        return sm


if __name__ == '__main__':
    DiabetesApp().run()