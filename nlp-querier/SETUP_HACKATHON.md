# 🚀 Quick Setup Guide for genai-hackathon-25

## Step-by-Step Setup for Your Analytics Agent

### 1. 📋 Copy Environment File
```bash
cp .env.example .env
```

Your `.env` file should contain:
```bash
# Your hackathon project
GOOGLE_CLOUD_PROJECT=genai-hackathon-25

# Your PostgreSQL database (update with your details)
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Vertex AI settings (defaults are fine)
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=text-bison@002
LOG_LEVEL=INFO
```

### 2. 🔐 Authenticate with Google Cloud

```powershell
# Set your project
gcloud config set project genai-hackathon-25

# Authenticate for application default credentials (KEY STEP)
gcloud auth application-default login

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com
```

### 3. 🗄️ Setup PostgreSQL Database

Choose one option:

#### Option A: Local PostgreSQL
```bash
# Install PostgreSQL locally
# Windows: Download from https://www.postgresql.org/download/windows/

# Create database
createdb analytics_db

# Update your .env:
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/analytics_db
```

#### Option B: Docker PostgreSQL (Recommended for testing)
```powershell
# Start PostgreSQL in Docker
docker run --name hackathon-postgres `
  -e POSTGRES_PASSWORD=hackathon2025 `
  -e POSTGRES_DB=analytics_db `
  -p 5432:5432 `
  -d postgres:15

# Update your .env:
DATABASE_URL=postgresql://postgres:hackathon2025@localhost:5432/analytics_db
```

### 4. 📦 Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt
```

### 5. 🧪 Test Your Setup

```powershell
# Quick test
python main.py --demo

# If that works, start the web interface
python main.py --interface streamlit
```

## ✅ Verification Checklist

- [ ] `.env` file created with `genai-hackathon-25`
- [ ] `gcloud auth application-default login` completed
- [ ] PostgreSQL running (local or Docker)
- [ ] Dependencies installed
- [ ] Demo runs successfully

## 🚨 Troubleshooting

### Authentication Issues
```powershell
# Check current authentication
gcloud auth list

# Check project setting
gcloud config get-value project

# Re-authenticate if needed
gcloud auth application-default login
```

### Database Issues
```powershell
# Test PostgreSQL connection
docker ps  # Check if container is running
# or
pg_isready -h localhost -p 5432  # Test local PostgreSQL
```

### Python Issues
```powershell
# Check Python version (needs 3.8+)
python --version

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

## 🎯 Next Steps

Once setup is complete:

1. **Test with demo**: `python main.py --demo`
2. **Web interface**: `python main.py --interface streamlit`
3. **CLI interface**: `python main.py --interface cli`

## 📝 Sample Questions to Try

- "Show me total sales by month"
- "What are the top 10 customers by revenue?"
- "Filter the previous results by region"
- "Show me average order value trends"

Your Analytics Agent is ready for the hackathon! 🎉