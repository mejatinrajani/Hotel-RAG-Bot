import os
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from groq import Groq
import random

from src.classifier import HotelIntentClassifier
from src.vector_store import HotelVectorStore

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
KB_FILE = os.path.join(DATA_DIR, "hotel_kb.json")


class HotelRAGOrchestrator:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", debug: bool = True):
        self.debug = debug
        self.model_name = model_name
        # Initialize Groq Client with Key Rotation
        api_keys = [
            os.getenv("GROQ_API_KEY"),
            os.getenv("GROQ_API_KEY_2"),
        ]
        
        valid_keys = [key for key in api_keys if key]
        
        if not valid_keys:
            raise ValueError("CRITICAL ERROR: No Groq API keys found in environment variables.")
            
        selected_key = random.choice(valid_keys)
        self.client = Groq(api_key=selected_key)
        if self.debug:
            print("[DEBUG] Initializing RAG pipeline components...")
            
        self.classifier = HotelIntentClassifier(debug=self.debug)
        self.vector_store = HotelVectorStore()
        self.vector_store.load_index()
        
        # Fallback local memory for local testing script only
        self.memory = []
        self.max_memory_turns = 5
        
        self._load_kb_config()

    def _load_kb_config(self):
        try:
            with open(KB_FILE, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
                
            self.retrieval_config = kb_data.get("retrieval_config", {})
            self.refusal_templates = kb_data.get("refusal_templates", {})
            self.rag_guardrails = kb_data.get("rag_guardrails", {})
            
            # Extract config with fallbacks
            self.top_k = self.retrieval_config.get("recommended_top_k", 5)
            self.similarity_threshold = self.retrieval_config.get("minimum_similarity_threshold", 0.75)
            
            if self.debug:
                print(f"[DEBUG] Config loaded: top_k={self.top_k}, threshold={self.similarity_threshold}")
                
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error loading KB config: {e}")
            self.retrieval_config, self.refusal_templates, self.rag_guardrails = {}, {}, {}
            self.top_k, self.similarity_threshold = 5, 0.75

    def _update_memory(self, query: str, response: str, is_db_drive: bool = False):
        # Skip local state tracking if FastAPI is running database updates
        if is_db_drive:
            return
        self.memory.append({"role": "user", "content": query})
        self.memory.append({"role": "assistant", "content": response})
        if len(self.memory) > self.max_memory_turns * 2:
            self.memory = self.memory[-(self.max_memory_turns * 2):]

    def _get_memory_context(self, history: List[Dict[str, str]] = None) -> str:
        active_history = history if history is not None else self.memory
        if not active_history:
            return ""
        return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in active_history])

    def _context_sufficient(self, query: str, context_chunks: List[Dict], history: List[Dict[str, str]] = None) -> bool:
        if not self.retrieval_config.get("enable_context_sufficiency_check", True):
            return True

        context_str = "\n".join([c.get("text", "") for c in context_chunks])
        memory_str = self._get_memory_context(history)
        
        prompt = f"""
        Evaluate if the provided Context contains sufficient specific information to answer the User Query.
        Consider recent conversation history if provided.
        
        You must return a JSON object matching this schema:
        {{
            "sufficient": true/false,
            "reason": "string explanation"
        }}

        Recent Conversation:
        {memory_str}
        
        Context:
        {context_str}
        
        User Query: "{query}"
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            if self.debug:
                print(f"[DEBUG] Sufficiency Check: {result}")
            return result.get("sufficient", False)
        except Exception as e:
            if self.debug: print(f"[DEBUG] Sufficiency check error: {e}")
            return False

    def _validate_answer(self, query: str, context_chunks: List[Dict], generated_answer: str, history: List[Dict[str, str]] = None) -> bool:
         if not self.retrieval_config.get("enable_answer_validation", True):
            return True

         context_str = "\n".join([c.get("text", "") for c in context_chunks])
         memory_str = self._get_memory_context(history)

         prompt = f"""
         Verify that EVERY factual claim in the Generated Answer is explicitly supported by the Retrieved Context.
         Consider recent conversation history if relevant.
         
         You must return a JSON object matching this schema:
         {{
             "grounded": true/false,
             "reason": "string explanation"
         }}

         Recent Conversation:
         {memory_str}
         
         Retrieved Context:
         {context_str}
         
         User Query: "{query}"
         
         Generated Answer: "{generated_answer}"
         """
         try:
             response = self.client.chat.completions.create(
                 messages=[{"role": "user", "content": prompt}],
                 model=self.model_name,
                 temperature=0.0,
                 response_format={"type": "json_object"}
             )
             result = json.loads(response.choices[0].message.content)
             if self.debug:
                 print(f"[DEBUG] Validation Check: {result}")
             return result.get("grounded", False)
         except Exception as e:
             if self.debug: print(f"[DEBUG] Answer validation error: {e}")
             return False

    def _build_generation_prompt(self, query: str, context_chunks: List[Dict], history: List[Dict[str, str]] = None) -> str:
        context_str = "\n\n".join([
            f"Source Segment [{i+1}]:\nCategory: {c.get('category', 'N/A')}\nIntent: {c.get('intent', 'N/A')}\nSource Section: {c.get('source_section', 'N/A')}\nContent: {c.get('text', '')}"
            for i, c in enumerate(context_chunks)
        ])
        
        memory_str = self._get_memory_context(history)
        
        return f"""
You are a professional, accurate concierge AI agent for our luxury 5-star hotel named "The Regal Aurum". 
Your objective is to answer the User Query using ONLY the verified facts provided in the Context Segments below.
Consider the Recent Conversation history to understand references (like "it", "that room").

CRITICAL INTEGRITY INSTRUCTIONS:
1. Rely strictly on the provided Context Segments. Do not assume, extrapolate, or use external training data.
2. If the Context Segments do not contain sufficient specific details, politely state that you do not possess that information.
3. Keep your tone helpful, elegant, and definitive. Do not mention "Context Segments", "database", or "system constraints".
4. If the user asks for your name, who you are, or what you do, you must reply: "I am the AI Digital Concierge for The Regal Aurum. I am here to assist you with room inquiries, amenities, hotel policies, and making your stay as luxurious as possible."

Recent Conversation:
{memory_str}

Context Segments:
{context_str}

User Query: "{query}"

Answer:
"""

    def process_query(self, query: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Processes a user query through the full RAG pipeline.
        Passing an explicit 'history' list makes this call state-free and multi-user safe for FastAPI.
        """
        is_db_driven = history is not None
        active_history = history if is_db_driven else self.memory

        if self.debug:
            print(f"\n[DEBUG] Processing Query: '{query}' (Mode: {'FastAPI/DB' if is_db_driven else 'Local CLI'})")
            
        # 1. Intent Classification
        memory_context = self._get_memory_context(active_history)
        query_for_classification = f"Recent History:\n{memory_context}\n\nCurrent Query: {query}" if memory_context else query
        classification = self.classifier.classify_intent(query_for_classification)
        detected_intent = classification.get("intent", "general_information")
        confidence = classification.get("confidence", 0.0)
        
        if self.debug:
            print(f"[DEBUG] Classified Intent: {detected_intent} (Confidence: {confidence:.2f})")

        # Dynamic Threshold based on confidence
        current_threshold = self.similarity_threshold
        if confidence < 0.60:
             current_threshold = max(0.40, self.similarity_threshold) 
             if self.debug: print(f"[DEBUG] Low confidence, keeping threshold at {current_threshold}")

        # Identity & Greeting Short-Circuit 
        if detected_intent in ["greeting", "identity"]:
            if self.debug: print(f"[DEBUG] Short-circuiting vector search for intent: {detected_intent}")
            
            # Skip FAISS completely and ask the LLM directly
            identity_prompt = f"""
            You are the official AI Digital Concierge for 'The Regal Aurum', a luxury 5-star hotel.
            The user just said: "{query}"
            
            If they said hello, greet them warmly and offer assistance with their stay.
            If they asked who you are, introduce yourself as the AI Digital Concierge for The Regal Aurum.
            If they asked what you can do or how you can help, briefly list your capabilities (e.g., answering questions about room pricing, check-out times, amenities, pet policies, and hotel rules).
            Keep it brief, elegant, and highly professional.
            """
            try:
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": identity_prompt}],
                    model=self.model_name,
                    temperature=0.3
                )
                generated_answer = response.choices[0].message.content.strip()
                self._update_memory(query, generated_answer, is_db_driven)
                return {
                    "response": generated_answer,
                    "intent": detected_intent,
                    "confidence": confidence,
                    "chunks_retrieved": 0,
                    "status": "success"
                }
            except Exception as e:
                pass 
        
        # --- Identity, Greeting & Moderation Short-Circuit ---
        if detected_intent == "inappropriate_query":
            if self.debug: print("[DEBUG] Short-circuiting for inappropriate query.")
            msg = "I am a professional digital concierge for The Regal Aurum. I am here to exclusively assist you with hotel-related inquiries, reservations, and amenities. How may I help you with your stay today?"
            self._update_memory(query, msg, is_db_driven)
            return {
                "response": msg,
                "intent": detected_intent,
                "confidence": confidence,
                "chunks_retrieved": 0,
                "status": "refused_inappropriate"
            }

        # 2. Vector Retrieval
        query_for_retrieval = query
        if len(active_history) >= 2:
            query_for_retrieval += f" (Context: {active_history[-2]['content']})"
        
        retrieved_chunks = self.vector_store.search(
            query=query_for_retrieval,
            top_k=self.top_k,
            similarity_threshold=current_threshold,
            user_intent=detected_intent
        )
        
        if self.debug:
            print(f"[DEBUG] Retrieved {len(retrieved_chunks)} chunks.")
            if retrieved_chunks: print(f"[DEBUG] Top Score: {retrieved_chunks[0].get('reranked_score', 0):.4f}")

        # 3. Guardrail: Empty Results
        if not retrieved_chunks:
            msg = self.refusal_templates.get("information_not_found", "Information not found.")
            self._update_memory(query, msg, is_db_driven)
            return {
                "response": msg,
                "intent": detected_intent,
                "confidence": confidence,
                "chunks_retrieved": 0,
                "status": "refused_insufficient_context"
            }
            
        # 4. Guardrail: Negative Knowledge Short-Circuit
        top_chunk = retrieved_chunks[0]
        if top_chunk.get("category") == "unsupported_information" or top_chunk.get("category") == "negative_knowledge":
            if self.debug: print("[DEBUG] Guardrail Triggered: Negative Knowledge Match.")
            msg = top_chunk.get("text", self.refusal_templates.get("unsupported_request", "Request not supported."))
            self._update_memory(query, msg, is_db_driven)
            return {
                "response": msg,
                "intent": detected_intent,
                "confidence": confidence,
                "chunks_retrieved": len(retrieved_chunks),
                "status": "refused_negative_knowledge"
            }
            
        # 5. Guardrail: Context Sufficiency
        is_sufficient = self._context_sufficient(query, retrieved_chunks, active_history)
        if not is_sufficient:
            if self.debug: print("[DEBUG] Guardrail Triggered: Context Insufficient.")
            msg = self.refusal_templates.get("context_insufficient", "Insufficient context.")
            self._update_memory(query, msg, is_db_driven)
            return {
                 "response": msg,
                 "intent": detected_intent,
                 "confidence": confidence,
                 "chunks_retrieved": len(retrieved_chunks),
                 "status": "refused_insufficient_context"
            }

        # 6. Generation
        generation_prompt = self._build_generation_prompt(query, retrieved_chunks, active_history)
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": generation_prompt}],
                model=self.model_name,
                temperature=0.0
            )
            generated_answer = response.choices[0].message.content.strip()
            
            # 7. Guardrail: Answer Validation
            is_valid = self._validate_answer(query, retrieved_chunks, generated_answer, active_history)
            if not is_valid:
                 if self.debug: print("[DEBUG] Guardrail Triggered: Answer Validation Failed.")
                 msg = self.refusal_templates.get("context_insufficient", "Insufficient context to validate answer.")
                 self._update_memory(query, msg, is_db_driven)
                 return {
                     "response": msg,
                     "intent": detected_intent,
                     "confidence": confidence,
                     "chunks_retrieved": len(retrieved_chunks),
                     "status": "refused_answer_validation"
                 }
                 
            self._update_memory(query, generated_answer, is_db_driven)
            return {
                "response": generated_answer,
                "intent": detected_intent,
                "confidence": confidence,
                "chunks_retrieved": len(retrieved_chunks),
                "status": "success"
            }
            
        except Exception as e:
            if self.debug: print(f"[DEBUG] Critical Generation Error: {str(e)}")
            msg = self.refusal_templates.get("live_data_unavailable", "System error.")
            return {
                "response": msg,
                "intent": detected_intent,
                "confidence": confidence,
                "chunks_retrieved": len(retrieved_chunks),
                "status": "generation_failure"
            }

if __name__ == "__main__":
    orchestrator = HotelRAGOrchestrator(debug=True)
    
    test_queries = [
        "What time is check-out?",
        "How much is early check-in before 7 AM?",
        "Can I bring my cat?",
        "What is the price of the Premier Room?",
        "What is the price of the Premier Room in December?",
        "Can I get a payment link to lock in a suite?",
        "Can you change my booking for tomorrow?"
    ]
    
    for q in test_queries:
        res = orchestrator.process_query(q)
        print(f"\nUser Query: {q}")
        print(f"Pipeline Response: {res['response']}")
        print(f"Status Flags: {res['status']} | Intent: {res['intent']}")
        print("-" * 60)