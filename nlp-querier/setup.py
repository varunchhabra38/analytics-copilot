#!/usr/bin/env python3
"""
Setup script for NLP Querier Analytics Agent.

This script helps users configure the simplified PostgreSQL + Vertex AI setup.
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_gcloud_cli():
    """Check if gcloud CLI is installed."""
    try:
        result = subprocess.run(['gcloud', '--version'], 
                              capture_output=True, text=True, check=True)
        print("✅ Google Cloud CLI installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Google Cloud CLI not found")
        print("Install from: https://cloud.google.com/sdk/docs/install")
        return False


def check_postgresql():
    """Check if PostgreSQL tools are available."""
    try:
        result = subprocess.run(['pg_isready', '--version'], 
                              capture_output=True, text=True, check=True)
        print("✅ PostgreSQL client tools available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  PostgreSQL client tools not found")
        print("Install PostgreSQL or just the client tools")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def create_env_file():
    """Create .env file from user input."""
    env_file = Path('.env')
    
    if env_file.exists():
        response = input("\n.env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("⏭️  Skipping .env creation")
            return True
    
    print("\n📝 Creating .env configuration file...")
    
    # Get database URL
    print("\n🗄️  Database Configuration:")
    print("Enter your PostgreSQL connection details:")
    
    db_host = input("Host (default: localhost): ") or "localhost"
    db_port = input("Port (default: 5432): ") or "5432"
    db_user = input("Username: ")
    db_password = input("Password: ")
    db_name = input("Database name: ")
    
    if not all([db_user, db_password, db_name]):
        print("❌ Database configuration incomplete")
        return False
    
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Get Google Cloud project
    print("\n☁️  Google Cloud Configuration:")
    gcp_project = input("Google Cloud Project ID: ")
    
    if not gcp_project:
        print("❌ Google Cloud Project ID is required")
        return False
    
    # Optional settings
    print("\n⚙️  Optional Settings (press Enter for defaults):")
    vertex_location = input("Vertex AI Location (default: us-central1): ") or "us-central1"
    vertex_model = input("Vertex AI Model (default: text-bison@002): ") or "text-bison@002"
    
    # Write .env file
    env_content = f"""# Database Configuration
DATABASE_URL={database_url}

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT={gcp_project}

# Optional: Vertex AI Configuration
VERTEX_AI_LOCATION={vertex_location}
VERTEX_AI_MODEL={vertex_model}
AI_TEMPERATURE=0.1

# Optional: Application Settings
MAX_RETRIES=3
OUTPUT_DIR=./output
LOG_LEVEL=INFO
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    print("\n🔗 Testing database connection...")
    try:
        from utils.db import create_database_manager
        
        db_manager = create_database_manager()
        if db_manager.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def authenticate_gcloud():
    """Guide user through Google Cloud authentication."""
    print("\n🔐 Google Cloud Authentication:")
    print("You need to authenticate with Google Cloud to use Vertex AI.")
    print("This will open a browser window for authentication.")
    
    response = input("Run 'gcloud auth application-default login' now? (Y/n): ")
    if response.lower() in ['', 'y', 'yes']:
        try:
            subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True)
            print("✅ Google Cloud authentication successful")
            return True
        except subprocess.CalledProcessError:
            print("❌ Google Cloud authentication failed")
            return False
    else:
        print("⏭️  Skipping authentication (you can run it manually later)")
        return True


def main():
    """Main setup process."""
    print("🚀 NLP Querier Analytics Agent Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Checking Google Cloud CLI", check_gcloud_cli),
        ("Checking PostgreSQL", check_postgresql),
        ("Installing dependencies", install_dependencies),
        ("Creating configuration", create_env_file),
        ("Authenticating Google Cloud", authenticate_gcloud),
        ("Testing database connection", test_database_connection),
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            results.append((step_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print("=" * 50)
    
    all_passed = True
    for step_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {step_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the demo: python main.py --demo")
        print("2. Start the web interface: python main.py --interface streamlit")
        print("3. Use CLI: python main.py --interface cli")
    else:
        print("\n⚠️  Setup completed with issues.")
        print("Please resolve the failed steps above and try again.")
        print("\nFor help, check the README.md or create an issue.")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()