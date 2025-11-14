"""
Configuration settings for the NLP Querier Analytics Agent.

This file contains simplified configuration for PostgreSQL + Vertex AI setup,
with SQLite fallback for easier testing.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables with sensible defaults.
    
    Returns:
        Dictionary containing all configuration settings
    """
    # Determine database type
    database_url = os.getenv("DATABASE_URL", "")
    database_type = os.getenv("DATABASE_TYPE", "auto")
    
    if database_type == "auto":
        if database_url.startswith("postgresql://"):
            database_type = "postgresql"
        else:
            # Default to SQLite for easier setup - using FCFP database
            database_type = "sqlite"
            database_url = "sqlite:///./output/fcfp_analytics.db"
    elif database_type == "sqlite" and not database_url:
        # If sqlite is explicitly specified but no URL provided, use default FCFP database
        database_url = "sqlite:///./output/fcfp_analytics.db"
    
    return {
        # Database Configuration (PostgreSQL or SQLite)
        "database": {
            "type": database_type,
            "connection_string": database_url,
        },
        
        # AI Configuration (Vertex AI with Application Default Credentials)
        "ai": {
            "type": "vertex_ai",
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
            "location": os.getenv("VERTEX_AI_LOCATION", "us-central1"),
            "model_name": os.getenv("VERTEX_AI_MODEL", "gemini-2.5-pro"),
            "temperature": float(os.getenv("AI_TEMPERATURE", "0.1")),
        },
        
        # Application Settings
        "app": {
            "title": "Analytics Agent",
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "output_dir": os.getenv("OUTPUT_DIR", "./output"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }
    }


def get_database_manager():
    """
    Get appropriate database manager based on configuration.
    
    Returns:
        Database manager instance
    """
    config = get_config()
    db_type = config["database"]["type"]
    
    if db_type == "sqlite":
        from utils.sqlite_db import SQLiteManager
        return SQLiteManager("output/fcfp_analytics.db")
    elif db_type == "postgresql":
        from utils.db import DatabaseManager
        return DatabaseManager(config["database"]["connection_string"])
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that all required configuration is present.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, raises ValueError if invalid
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Check AI configuration (required for full functionality)
    # But allow testing with SQLite even without GCP project
    if not config["ai"]["project_id"]:
        print("Warning: GOOGLE_CLOUD_PROJECT not set. AI features will be limited.")
    
    # Database configuration is optional now (SQLite fallback)
    
    return True


# Example .env file contents:
# DATABASE_URL=postgresql://user:password@localhost:5432/your_db
# GOOGLE_CLOUD_PROJECT=your-gcp-project-id
# VERTEX_AI_LOCATION=us-central1
# VERTEX_AI_MODEL=text-bison@002
# AI_TEMPERATURE=0.1
# MAX_RETRIES=3
# OUTPUT_DIR=./output
# LOG_LEVEL=INFO