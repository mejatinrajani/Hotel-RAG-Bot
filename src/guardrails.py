import re

class HotelGuardrails:
    """
    Zero-Trust Security layer for the Hotel RAG Pipeline.
    Evaluates queries before they hit the vector database and validates answers
    before they are returned to the user.
    """

    def __init__(self):
        # 1. Negative Knowledge Definitions
        # Things the bot should instantly refuse without even searching the database
        self.forbidden_topics = [
            "payment link",
            "credit card",
            "cvv",
            "bank account",
            "transaction",
            "override",
            "ignore previous instructions",
            "system prompt",
            "database",
            "wi-fi password",
            "manager password",
            "discount code",
            "coupon",
            "cancel my reservation",
            "book a room",
            "upgrade my room"
        ]

        # Regex pattern to catch common prompt injection attempts
        self.injection_pattern = re.compile(
            r"(ignore previous|system prompt|you are a|override|sudo |admin access)", 
            re.IGNORECASE
        )

    def check_negative_knowledge(self, query: str) -> dict:
        """
        Fast-fail check for forbidden topics and basic prompt injections.
        Runs BEFORE embedding or vector search to save API quota.
        """
        query_lower = query.lower()

        # Check for Prompt Injection
        if self.injection_pattern.search(query_lower):
            return {
                "safe": False,
                "reason": "refused_security_violation",
                "message": "I cannot fulfill requests that attempt to alter my instructions."
            }

        # Check for explicitly forbidden topics (Negative Knowledge)
        for topic in self.forbidden_topics:
            if topic in query_lower:
                # If they ask for payment/booking/canceling, give a specific operational refusal
                if topic in ["payment link", "credit card", "cancel my reservation", "book a room"]:
                    return {
                        "safe": False,
                        "reason": "refused_negative_knowledge",
                        "message": "The assistant cannot create, modify, cancel, confirm, upgrade, downgrade, or manage hotel reservations. Payment links, payment gateway URLs, and secure portals are not stored in this knowledge base."
                    }
                else:
                    return {
                        "safe": False,
                        "reason": "refused_insufficient_context",
                        "message": "I couldn't find that information in the hotel knowledge base. Please contact hotel staff for assistance."
                    }

        return {"safe": True, "reason": None, "message": None}

    def validate_llm_sufficiency(self, llm_response: str) -> bool:
        """
        Checks if the LLM's generated response indicates it couldn't find the answer
        despite passing the initial vector search threshold.
        """
        failure_phrases = [
            "does not contain",
            "i do not have",
            "is not mentioned",
            "cannot find",
            "is not provided in the context"
        ]
        
        response_lower = llm_response.lower()
        for phrase in failure_phrases:
            if phrase in response_lower:
                return False
                
        return True

    def validate_formatting(self, response: str) -> str:
        """
        Ensures the final response doesn't leak internal RAG context markers
        like [Document 1] or generic AI filler phrases.
        """
        # Clean up common LLM artifacts
        clean_response = re.sub(r'\[Document \d+\]', '', response)
        clean_response = re.sub(r'Based on the provided context, ', '', clean_response, flags=re.IGNORECASE)
        clean_response = re.sub(r'According to the knowledge base, ', '', clean_response, flags=re.IGNORECASE)
        
        return clean_response.strip()