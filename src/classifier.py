import os
import json
from pydantic import BaseModel, Field
import google.generativeai as genai

# Configure the Gemini API client from environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Paths for data dependencies
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
KB_FILE = os.path.join(DATA_DIR, "hotel_kb.json")

class IntentClassificationResult(BaseModel):
    intent: str = Field(
        description="The exact matched intent name from the allowed supported_intents list."
    )
    confidence: float = Field(
        description="The confidence score of the classification between 0.0 and 1.0."
    )

class HotelIntentClassifier:
    def __init__(self, model_name: str = "gemini-2.5-flash-lite", debug: bool = False):
        """
        Initializes the classifier by dynamically binding intents from the knowledge base,
        building the structural prompt, and instantiating the Gemini model once for reuse.
        """
        self.model_name = model_name
        self.debug = debug
        self.supported_intents = []
        
        # 1. Load intents from KB
        self._load_intents_from_kb()
        
        # 2. Build system instruction prompt dynamically
        system_instruction = self._build_system_instruction()
        
        # 3. Initialize Gemini model once at startup
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

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
        """Constructs the prompt instructing Gemini to strictly choose valid intents."""
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

Few-Shot Multilingual Examples for Accuracy (English, Hindi, Hinglish):
- Query: "Pool kitne baje band hota hai?" -> "amenity_query"
- Query: "Can I bring my dog?" -> "pet_policy"
- Query: "Smoking allowed hai?" -> "smoking_policy"
- Query: "What is the security deposit?" -> "security_deposit"
- Query: "Airport pickup available hai?" -> "airport_transfer"
- Query: "What is the price of the Premier Room?" -> "pricing_query"
- Query: "Suite cost kitna hai?" -> "pricing_query"
- Query: "Can you change my booking for tomorrow?" -> "general_information"
- Query: "Send me the link to pay for my room." -> "general_information"
- Query: "What will the room cost during New Year's 2027?" -> "general_information"
"""

    def classify_intent(self, query: str) -> dict:
        """
        Classifies the user query using the initialized Gemini model instance, validates the
        output intent, and applies strict confidence routing logic.
        """
        try:
            response = self.model.generate_content(
                f"Classify this query: '{query}'",
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=IntentClassificationResult,
                    temperature=0.0
                )
            )
            
            result_data = json.loads(response.text)
            intent = result_data.get("intent")
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