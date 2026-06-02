import os
import sys
from dotenv import load_dotenv

# 1. Load environment variables from .env FIRST
load_dotenv()

# 2. NOW import the local modules (which rely on the API key being loaded)
from src.rag_pipeline import HotelRAGOrchestrator

# ANSI escape codes for a beautiful terminal UI
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}======================================================
    THE REGAL AURUM - AI CONCIERGE (CLI TERMINAL)
======================================================
* Type your questions naturally.
* Guardrail interventions will be highlighted in RED.
* Type 'exit' or 'quit' to terminate the session.
======================================================{Colors.RESET}
    """
    print(banner)

def main():
    # Final check to ensure the key was loaded successfully
    if not os.environ.get("GEMINI_API_KEY"):
        print(f"{Colors.RED}CRITICAL ERROR: GEMINI_API_KEY not found.{Colors.RESET}")
        print("Ensure your .env file is in the root directory and formatted as:\nGEMINI_API_KEY=your_key_here")
        sys.exit(1)

    print_banner()
    
    print(f"{Colors.YELLOW}Booting up the Zero-Trust RAG Orchestrator...{Colors.RESET}")
    orchestrator = HotelRAGOrchestrator(debug=True)
    print(f"{Colors.GREEN}System Online. Knowledge Base Loaded.{Colors.RESET}\n")

    while True:
        try:
            user_input = input(f"{Colors.BLUE}{Colors.BOLD}Guest: {Colors.RESET}")
            
            if not user_input.strip():
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n{Colors.YELLOW}Terminating session. Goodbye!{Colors.RESET}")
                break

            result = orchestrator.process_query(user_input)
            
            status = result.get('status', 'unknown')
            response = result.get('response', 'Error processing request.')
            intent = result.get('intent', 'unknown')
            chunks = result.get('chunks_retrieved', 0)
            
            print("")
            
            if status == "success":
                print(f"{Colors.GREEN}{Colors.BOLD}Agent: {Colors.RESET}{response}")
            else:
                print(f"{Colors.RED}{Colors.BOLD}[GUARDRAIL: {status.upper()}]{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}Agent: {Colors.RESET}{response}")

            print(f"{Colors.CYAN}[Routing: {intent} | Context Chunks Used: {chunks}]{Colors.RESET}\n")

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Session interrupted by user. Exiting...{Colors.RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Colors.RED}Critical Application Error: {str(e)}{Colors.RESET}\n")

if __name__ == "__main__":
    main()