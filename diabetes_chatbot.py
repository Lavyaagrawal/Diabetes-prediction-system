"""
Diabetes Health Assistant Chatbot
- Provides information about diabetes management and health advice
- Connects to OpenRouter API for intelligent responses
- Maintains conversation history for context
"""

import os
import logging
import threading
from datetime import datetime
import uuid
import time
import random
import requests
from typing import Optional, Dict, List, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("diabetes_chatbot")


class OpenRouterChatbot:
    """
    Diabetes chatbot with OpenRouter API integration
    - Uses OpenRouter API for intelligent responses
    - Maintains conversation history
    - Provides comprehensive fallback responses
    """

    def __init__(self, api_key: str = None, model: str = "anthropic/claude-3-opus", debug: bool = False):
        # Configuration
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set it in the constructor or OPENROUTER_API_KEY environment variable.")
        
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.session_id = f"session_{str(uuid.uuid4())}"
        self.conversation_history = []
        self.debug = debug
        self._init_knowledge_base()
        self.has_internet = self._check_internet_connection()
        self.username = None
        self.response_cache = {}

        # System prompt
        self.system_prompt = """You are a knowledgeable and supportive diabetes health assistant.
        Your goal is to provide accurate, helpful information about diabetes management, 
        symptoms, treatments, diet, exercise, and self-care.
        Always be empathetic, clear, and provide practical advice.
        Keep responses concise (2-3 paragraphs maximum) and easy to understand.
        Do not provide specific medical advice - remind users to consult healthcare professionals for personalized guidance."""

        # Add suggested queries
        self.suggested_queries = [
            "What is diabetes?",
            "What are the symptoms of diabetes?",
            "How can I manage my blood sugar levels?",
            "What foods should I avoid with diabetes?",
            "What is the difference between Type 1 and Type 2 diabetes?",
            "How does exercise help with diabetes?",
            "What are the complications of diabetes?",
            "How often should I check my blood sugar?",
            "What are normal blood sugar levels?",
            "Can diabetes be cured?",
            "What should I do if my blood sugar is too high?",
            "What medications are used to treat diabetes?",
            "How can I prevent diabetes complications?",
            "What is gestational diabetes?",
            "How does stress affect diabetes?"
        ]

        logger.info(f"OpenRouter Chatbot initialized with session ID: {self.session_id}")

    def set_username(self, username: str):
        """Set the username for personalization"""
        self.username = username
        if username:
            self.session_id = f"user_{username.split()[0].lower()}"
            logger.info(f"Username set to: {username} (Session ID: {self.session_id})")

    def get_suggested_queries(self, count: int = 3) -> List[str]:
        """Get randomly selected suggested queries"""
        if count > len(self.suggested_queries):
            count = len(self.suggested_queries)
        return random.sample(self.suggested_queries, count)

    def _check_internet_connection(self) -> bool:
        """Check if internet connection is available"""
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            logger.warning("No internet connection available")
            return False
        except Exception as e:
            logger.warning(f"Error checking internet connection: {str(e)}")
            return False

    def generate_response(self, user_message: str) -> str:
        """Generate response using OpenRouter API with fallback to local knowledge"""
        if not self.has_internet:
            return self._get_fallback_response(user_message)

        try:
            # Prepare conversation history for the API
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history (last 5 messages for context)
            for msg in self.conversation_history[-5:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://your-app-domain.com",  # Replace with your actual domain
                "X-Title": "Diabetes Health Assistant"  # Optional app name
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
                # Add to conversation history
                self._add_to_history("user", user_message)
                self._add_to_history("assistant", ai_response)
                
                return ai_response
            else:
                logger.error(f"OpenRouter API error: {response.status_code}")
                return self._get_fallback_response(user_message)

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._get_fallback_response(user_message)

    def _init_knowledge_base(self):
        """Initialize the local knowledge base for fallback responses"""
        self.diabetes_info = {
            "diabetes": "Diabetes is a chronic health condition that affects how your body turns food into energy. If you have diabetes, your body either doesn't make enough insulin or can't use the insulin it makes as well as it should.",
            "symptoms": "Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, blurred vision, slow-healing sores, and frequent infections.",
            "type 1": "Type 1 diabetes is an autoimmune disease where the body's immune system attacks and destroys the cells in the pancreas that make insulin. It's usually diagnosed in children, teens, and young adults.",
            "type 2": "Type 2 diabetes occurs when your body doesn't use insulin properly. It's the most common type of diabetes and is often related to lifestyle factors like obesity and lack of physical activity.",
            "food": "A diabetes-friendly diet includes plenty of non-starchy vegetables, lean proteins, healthy fats, and whole grains. It's important to limit refined carbs, sugary foods, and high-fat dairy or meat products.",
            "exercise": "Regular physical activity helps manage diabetes by improving insulin sensitivity, maintaining a healthy weight, and reducing stress. Aim for at least 150 minutes of moderate exercise per week.",
            "treatment": "Treatment for diabetes may include insulin therapy, oral medications, regular blood sugar monitoring, healthy eating, and regular exercise. The specific treatment plan depends on the type of diabetes.",
            "complications": "Diabetes complications can include heart disease, nerve damage (neuropathy), kidney damage, eye damage, foot damage, skin conditions, and Alzheimer's disease. Managing blood sugar can help prevent complications.",
            "blood sugar": "Normal blood sugar levels are generally between 70-99 mg/dL when fasting and less than 140 mg/dL two hours after eating. For people with diabetes, target ranges may vary based on individual factors.",
            "prevention": "Type 2 diabetes can often be prevented or delayed with lifestyle changes including maintaining a healthy weight, regular physical activity, eating a balanced diet, and not smoking.",
            "gestational": "Gestational diabetes develops during pregnancy and can increase the risk of complications for both mother and baby. It usually resolves after delivery, but increases the risk of type 2 diabetes later.",
            "medication": "Medications for diabetes include insulin, metformin, sulfonylureas, meglitinides, thiazolidinediones, DPP-4 inhibitors, GLP-1 receptor agonists, SGLT2 inhibitors, and more. Each works differently to control blood sugar.",
            "cure": "Currently, there is no cure for diabetes, but it can be managed effectively with the right treatment plan and lifestyle changes. Research for a cure is ongoing, especially for type 1 diabetes."
        }

        self.greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        self.farewells = ["bye", "goodbye", "farewell", "see you", "take care"]
        
        self.support_responses = [
            "Living with diabetes can be challenging, but you're not alone. Many people lead full, active lives with diabetes by managing it well.",
            "It's normal to feel overwhelmed sometimes. Taking one small step at a time in managing your diabetes can make a big difference.",
            "Remember that self-care is important. Make sure to take time for activities you enjoy and that help you relax.",
            "If you're feeling stressed about managing your diabetes, consider joining a support group or talking to a healthcare professional about your concerns."
        ]

    def _get_fallback_response(self, message: str) -> str:
        """Get fallback response from local knowledge base when API is unavailable"""
        message = message.lower()
        
        # Check for greetings
        if any(greeting in message for greeting in self.greetings):
            greeting = "Hello! I'm your diabetes health assistant. How can I help you today?"
            if self.username:
                greeting = f"Hello {self.username}! I'm your diabetes health assistant. How can I help you today?"
            return greeting

        # Check for farewells
        if any(farewell in message for farewell in self.farewells):
            return "Take care! Remember to maintain regular blood sugar checks and follow your healthcare plan."

        # Check for keywords in the knowledge base
        for key, response in self.diabetes_info.items():
            if key in message:
                return response

        # If message suggests emotional support is needed
        if any(word in message for word in ["worried", "scared", "anxious", "stressed", "overwhelmed"]):
            return random.choice(self.support_responses)

        # Default response
        return "I can provide information about diabetes management, including diet, exercise, symptoms, and treatments. How can I help you today?"

    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_conversation_summary(self) -> Dict:
        """Get summary of the conversation"""
        return {
            "session_id": self.session_id,
            "message_count": len(self.conversation_history),
            "history": self.conversation_history
        }

# For testing the chatbot directly
if __name__ == "__main__":
    print("Diabetes Chatbot Test Mode (OpenRouter)")
    chatbot = OpenRouterChatbot(debug=True)

    print("Type your questions about diabetes (or 'exit' to quit):")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit", "bye"]:
            break

        print("\nChatbot:", chatbot.generate_response(user_input))