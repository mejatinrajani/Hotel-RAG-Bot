import os
import json
from groq import Groq
import random

# Paths for data dependencies
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
KB_FILE = os.path.join(DATA_DIR, "hotel_kb.json")

class HotelIntentClassifier:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", debug: bool = False):
        """
        Initializes the Groq classifier by dynamically binding intents from the knowledge base,
        and setting up the fast Llama 3 API client.
        """
        self.model_name = model_name
        self.debug = debug
        self.supported_intents = []
        # Initialize Groq Client with Key Rotation
        api_keys = [
            os.getenv("GROQ_API_KEY_1"),
            os.getenv("GROQ_API_KEY_2"),
            os.getenv("GROQ_API_KEY_3")
        ]
        
        valid_keys = [key for key in api_keys if key]
        
        if not valid_keys:
            raise ValueError("CRITICAL ERROR: No Groq API keys found in environment variables.")
            
        selected_key = random.choice(valid_keys)
        self.client = Groq(api_key=selected_key)
        
        # 1. Load intents from KB
        self._load_intents_from_kb()
        
        # 2. Build system instruction prompt dynamically
        self.system_instruction = self._build_system_instruction()

    def _load_intents_from_kb(self):
        """Loads valid intents dynamically from hotel_kb.json to guarantee layer sync."""
        try:
            with open(KB_FILE, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            self.supported_intents = kb_data.get("supported_intents", [])
            
            if "general_information" not in self.supported_intents:
                self.supported_intents.append("general_information")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Failed to load hotel_kb.json: {str(e)}")
            self.supported_intents = ["general_information"]

    def _build_system_instruction(self) -> str:
        """Constructs the prompt instructing Llama to strictly choose valid intents."""
        intents_list_str = "\n".join([f"- {intent}" for intent in self.supported_intents])
        
        return f"""
You are a highly precise intent classification router for a guarded luxury hotel RAG assistant.
Your job is to analyze the user's input query and categorize it into exactly ONE of the following supported intents:

{intents_list_str}

CRITICAL ROUTING INSTRUCTIONS:
1. Match the intent based on semantic meaning rather than simple keyword overlapping. 
2. Explicitly handle static pricing questions (e.g., room costs, general price inquiries) using 'pricing_query'.
3. If the query requests active transaction/reservation management actions, external modifications, or live system checks (e.g., "book a room", "change my booking", "send payment link", "check open slots for tonight", "generate corporate quote"), you MUST classify the query as 'general_information'.
4. Do not invent any new intent strings. Your output must strictly match one of the items listed in the allowlist.

You MUST return ONLY a raw JSON object with no markdown formatting or extra text. It must match this exact schema:
{{
    "intent": "category_name",
    "confidence": 0.95
}}

Few-Shot Multilingual Examples for Accuracy (English, Hindi, Hinglish):
- Query: "Pool kitne baje band hota hai?" -> {{"intent": "amenity_query", "confidence": 0.98}}
- Query: "Can I bring my dog?" -> {{"intent": "pet_policy", "confidence": 0.99}}
- Query: "Smoking allowed hai?" -> {{"intent": "smoking_policy", "confidence": 0.97}}
- Query: "What is the security deposit?" -> {{"intent": "security_deposit", "confidence": 0.95}}
- Query: "Airport pickup available hai?" -> {{"intent": "airport_transfer", "confidence": 0.96}}
- Query: "What is the price of the Premier Room?" -> {{"intent": "pricing_query", "confidence": 0.99}}
- Query: "Suite cost kitna hai?" -> {{"intent": "pricing_query", "confidence": 0.98}}
- Query: "Can you change my booking for tomorrow?" -> {{"intent": "general_information", "confidence": 0.99}}
- Query: "Send me the link to pay for my room." -> {{"intent": "general_information", "confidence": 0.99}}
- Query: "What will the room cost during New Year's 2027?" -> {{"intent": "general_information", "confidence": 0.99}}
- Query: "Hi, hello there!" -> {{"intent": "greeting", "confidence": 0.99}}
- Query: "What is your name?" -> {{"intent": "identity", "confidence": 0.99}}
- Query: "Who are you?" -> {{"intent": "identity", "confidence": 0.98}}
- Query: "What can you do for me?" -> {{"intent": "identity", "confidence": 0.99}}
- Query: "How can you help?" -> {{"intent": "identity", "confidence": 0.99}}
- Query: "can i have sex at your hotel" -> {{"intent": "inappropriate_query", "confidence": 0.99}}
- Query: "you are stupid" -> {{"intent": "inappropriate_query", "confidence": 0.99}}
- Query: "tell me a dirty joke" -> {{"intent": "inappropriate_query", "confidence": 0.99}}
"""

    def classify_intent(self, query: str) -> dict:
        """
        Classifies the user query using the initialized Groq Llama 3 model instance, validates the
        output intent, and applies strict confidence routing logic.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": f"Classify this query: '{query}'"}
                ],
                model=self.model_name,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result_data = json.loads(response.choices[0].message.content)
            intent = result_data.get("intent", "general_information")
            confidence = float(result_data.get("confidence", 0.0))
            
            # Issue 5 Validation Layer: If output is invalid or hallucinated, fall back instantly
            if intent not in self.supported_intents:
                if self.debug:
                    print(f"[DEBUG] Invalid intent received: '{intent}'. Routing fallback.")
                return {"intent": "general_information", "confidence": 0.0}
                
            # Issue 1 Confidence Safety Guardrail: Preserve actual low confidence scores during a fallback
            if confidence < 0.60:
                if self.debug:
                    print(f"[DEBUG] Low confidence ({confidence}) for intent '{intent}'. Downgrading to general_information.")
                return {"intent": "general_information", "confidence": confidence}
                
            if self.debug:
                print(f"[DEBUG] Successful Classification | Query: '{query}' | Intent: '{intent}' | Confidence: {confidence}")
                
            return {
                "intent": intent,
                "confidence": confidence
            }

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error encountered during classification pipeline: {str(e)}")
            return {
                "intent": "general_information",
                "confidence": 0.0
            }

if __name__ == "__main__":
    classifier = HotelIntentClassifier(debug=True)
    print("Configured KB Intents in Memory:", classifier.supported_intents)
    
    # Quick local test
    test_res = classifier.classify_intent("kitne baje checkin hai?")
    print("Test Result:", test_res)