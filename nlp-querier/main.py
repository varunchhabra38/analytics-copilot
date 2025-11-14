"""
Main entry point for the NLP Querier Analytics Agent.

Simplified setup using PostgreSQL and Vertex AI with Application Default Credentials.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging(level: str = "INFO"):
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def run_streamlit():
    """Run the Streamlit chat interface."""
    import subprocess
    streamlit_path = project_root / "ui" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_path)])


def run_demo():
    """Run a simple demonstration of the Analytics Agent."""
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        from config import get_config, validate_config
        
        config = get_config()
        validate_config(config)
        
        logger.info("Starting NLP Querier Analytics Agent Demo")
        
        # Test database connection
        from utils.db import create_database_manager
        db_manager = create_database_manager(config["database"]["connection_string"])
        
        if not db_manager.test_connection():
            logger.error("Database connection failed. Please check your DATABASE_URL.")
            return
        
        print("=" * 60)
        print("NLP Querier Analytics Agent - Demo")
        print("=" * 60)
        print(f"Database: {config['database']['type']}")
        print(f"AI Provider: {config['ai']['type']}")
        print(f"Project: {config['ai']['project_id']}")
        print("=" * 60)
        
        # Import and run agent
        from agent.graph import run_agent_chat
        
        # Example conversation
        history = []
        
        # Example 1: Simple query
        question1 = "Show me total revenue by month"
        print(f"\nUser: {question1}")
        
        result1 = run_agent_chat(question1, history, config)
        print(f"Agent: {result1.get('summary', 'Processing...')}")
        
        if result1.get('sql'):
            print(f"Generated SQL: {result1['sql']}")
        
        # Update history
        history = result1.get('history', [])
        
        # Example 2: Follow-up query
        question2 = "Filter that by the EMEA region"
        print(f"\nUser: {question2}")
        
        result2 = run_agent_chat(question2, history, config)
        print(f"Agent: {result2.get('summary', 'Processing...')}")
        
        if result2.get('sql'):
            print(f"Generated SQL: {result2['sql']}")
        
        print("\n" + "=" * 60)
        print("Demo Complete! To run the interactive interface:")
        print("python main.py --interface streamlit")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"Error: {e}")
        print("\nPlease check your configuration:")
        print("1. Set DATABASE_URL environment variable")
        print("2. Set GOOGLE_CLOUD_PROJECT environment variable")
        print("3. Run: gcloud auth application-default login")


def run_cli():
    """Run the CLI interface for testing."""
    logger = logging.getLogger(__name__)
    
    try:
        from config import get_config, validate_config
        from agent.graph import run_agent_chat
        
        config = get_config()
        validate_config(config)
        
        print("LangGraph Analytics Agent - CLI Mode")
        print("Type 'quit' to exit")
        
        history = []
        
        while True:
            try:
                question = input("\nYour question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("Processing...")
                result = run_agent_chat(question, history, config)
                
                print(f"\nResponse: {result.get('summary', 'No summary available')}")
                
                if result.get('sql'):
                    print(f"SQL: {result['sql']}")
                
                if result.get('visualization_path'):
                    print(f"Chart: {result['visualization_path']}")
                
                # Update conversation history
                history = result.get('history', [])
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error processing question: {e}")
                print(f"Error: {e}")
    
    except Exception as e:
        logger.error(f"CLI startup error: {e}")
        print(f"Error: {e}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="NLP Querier Analytics Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --interface streamlit    # Web interface
  python main.py --interface cli         # Command line
  python main.py --demo                  # Quick demo
        """
    )
    
    parser.add_argument(
        "--interface", 
        choices=["streamlit", "cli"],
        default="streamlit",
        help="Interface to run (default: streamlit)"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a quick demonstration"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(log_level)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv is optional
    
    # Verify required environment variables
    required_vars = ["DATABASE_URL", "GOOGLE_CLOUD_PROJECT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nExample .env file:")
        print("DATABASE_URL=postgresql://user:password@localhost:5432/dbname")
        print("GOOGLE_CLOUD_PROJECT=your-gcp-project-id")
        print("\nSetup steps:")
        print("1. Create .env file with the above variables")
        print("2. Run: gcloud auth application-default login")
        print("3. Install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    
    # Display configuration
    if not args.debug:
        print("Configuration:")
        print(f"✅ Database: {os.getenv('DATABASE_URL', '').split('@')[0]}@***")
        print(f"✅ Google Cloud Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        print("✅ Using Application Default Credentials")
        print()
    
    # Run the selected interface
    try:
        if args.demo:
            run_demo()
        elif args.interface == "streamlit":
            run_streamlit()
        elif args.interface == "cli":
            run_cli()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting {args.interface}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
import argparse
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_streamlit():
    """Run the Streamlit chat interface."""
    import subprocess
    streamlit_path = project_root / "ui" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_path)])


def run_fastapi():
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "ui.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


def run_cli():
    """Run the CLI interface for testing."""
    from agent.graph import run_agent_chat
    
    print("LangGraph Analytics Agent - CLI Mode")
    print("Type 'quit' to exit")
    
    history = []
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            # Run the agent
            result = run_agent_chat(question, history)
            
            # Display results
            if result.get("clarification_needed"):
                print(f"\nClarification needed: {result.get('clarification_question')}")
                clarification = input("Your clarification: ").strip()
                # TODO: Continue with clarification
            else:
                print(f"\nSQL: {result.get('sql', 'No SQL generated')}")
                print(f"\nSummary: {result.get('summary', 'No summary available')}")
                
                if result.get('visualization_path'):
                    print(f"Visualization saved to: {result['visualization_path']}")
            
            # Update history
            history = result.get('history', history)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="LangGraph Analytics Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py streamlit          # Run Streamlit UI
  python main.py fastapi           # Run FastAPI server
  python main.py cli               # Run CLI interface
        """
    )
    
    parser.add_argument(
        "interface",
        choices=["streamlit", "fastapi", "cli"],
        default="streamlit",
        nargs="?",
        help="Interface to run (default: streamlit)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Setup environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verify required environment variables
    # For Google Cloud setup
    gcp_required_vars = ["GOOGLE_CLOUD_PROJECT"]
    gcp_missing = [var for var in gcp_required_vars if not os.getenv(var)]
    
    # For OpenAI (optional fallback)
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if gcp_missing and not openai_key:
        print("Error: Missing required environment variables:")
        print("For Google Cloud: GOOGLE_CLOUD_PROJECT")
        print("For OpenAI fallback: OPENAI_API_KEY") 
        print("\nRecommended setup for Google Cloud:")
        print("- GOOGLE_CLOUD_PROJECT=your-project-id")
        print("- GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json (optional)")
        print("- BIGQUERY_DATASET=your_dataset (optional)")
        print("\nPlease set them in your .env file or environment.")
        sys.exit(1)
    
    # Display configuration info
    if not args.debug:
        print("Configuration:")
        if os.getenv("GOOGLE_CLOUD_PROJECT"):
            print(f"✅ Google Cloud Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                print("✅ Service Account credentials configured")
            else:
                print("ℹ️  Using Application Default Credentials")
        if openai_key:
            print("✅ OpenAI API key available as fallback")
        print()
    
    # Run the selected interface
    try:
        if args.interface == "streamlit":
            run_streamlit()
        elif args.interface == "fastapi":
            run_fastapi()
        elif args.interface == "cli":
            run_cli()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting {args.interface}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()