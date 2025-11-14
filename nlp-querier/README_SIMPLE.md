# NLP Querier Analytics Agent

A simplified, production-ready LangGraph-based Analytics Agent that converts natural language to SQL queries using PostgreSQL and Google Vertex AI.

## ✅ Features

- **Natural Language → SQL**: Convert questions to optimized PostgreSQL queries
- **Conversational Interface**: Multi-turn conversations with context retention
- **Google Vertex AI Integration**: Advanced SQL generation with Application Default Credentials
- **PostgreSQL Focus**: Optimized for PostgreSQL databases
- **Streamlit UI**: Interactive chat interface
- **LangGraph Workflow**: Robust agent workflow with retry logic and clarification loops
- **Visualization**: Automatic chart generation from query results

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL database
- Google Cloud account with Vertex AI enabled

### 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd nlp-querier

# Install dependencies
pip install -r requirements.txt
```

### 3. Google Cloud Setup

```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate with Application Default Credentials
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 4. Configuration

Create a `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/your_database

# Google Cloud Configuration  
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Optional: Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=text-bison@002
AI_TEMPERATURE=0.1

# Optional: Application Settings
MAX_RETRIES=3
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

### 5. Run the Application

#### Streamlit Web Interface (Recommended)
```bash
python main.py --interface streamlit
```

#### Command Line Interface
```bash
python main.py --interface cli
```

#### Quick Demo
```bash
python main.py --demo
```

## 💬 Example Conversations

### Simple Analytics Query
```
User: Show me total revenue by month
Agent: I'll analyze your revenue data by month...

Generated SQL: 
SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(total_amount) as total_revenue
FROM orders 
GROUP BY month 
ORDER BY month;
```

### Follow-up with Context
```
User: Filter that by the EMEA region
Agent: I'll filter the previous revenue analysis for EMEA region...

Generated SQL:
SELECT 
    DATE_TRUNC('month', o.order_date) as month,
    SUM(o.total_amount) as total_revenue
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'EMEA'
GROUP BY month 
ORDER BY month;
```

## 🏗️ Architecture

### Core Components

- **`agent/`**: LangGraph workflow and nodes
  - `state.py`: Conversation state management
  - `graph.py`: LangGraph workflow definition
  - `nodes/`: Individual workflow nodes (intent detection, SQL generation, etc.)
  - `tools/`: Reusable tools (schema lookup, SQL execution, etc.)

- **`ui/`**: User interfaces
  - `streamlit_app.py`: Interactive web chat interface

- **`utils/`**: Utilities
  - `db.py`: Simplified PostgreSQL connection management
  - `logging.py`: Logging configuration

### Workflow

1. **Intent Detection**: Analyze user question for ambiguity
2. **Schema Lookup**: Retrieve relevant database schema
3. **SQL Generation**: Convert to PostgreSQL using Vertex AI
4. **SQL Validation**: Ensure query safety and correctness
5. **Execution**: Run query against database
6. **Visualization**: Generate charts from results
7. **Summary**: Provide natural language explanation

## 🛠️ Development

### Project Structure
```
nlp-querier/
├── agent/
│   ├── graph.py              # LangGraph workflow
│   ├── state.py              # Agent state management  
│   ├── nodes/                # Workflow nodes
│   └── tools/                # Reusable tools
├── ui/
│   └── streamlit_app.py      # Web interface
├── utils/
│   ├── db.py                 # Database utilities
│   └── logging.py            # Logging setup
├── config.py                 # Configuration management
├── main.py                   # Entry point
└── requirements.txt          # Dependencies
```

### Key Dependencies

- **LangGraph**: Agent workflow orchestration
- **Google Cloud AI Platform**: Vertex AI for SQL generation
- **psycopg2-binary**: PostgreSQL connectivity
- **Streamlit**: Web interface
- **Pandas**: Data manipulation
- **Matplotlib**: Visualization

### Testing

```bash
# Test database connection
python -c "from utils.db import create_database_manager; print(create_database_manager().test_connection())"

# Test Vertex AI connection
python -c "from agent.tools.sql_gen_tool import create_sql_gen_tool; print('AI tools loaded successfully')"

# Run demo
python main.py --demo
```

## 🔧 Configuration Options

### Database Types
- **PostgreSQL** (primary): Full-featured production database
- **SQLite** (development): Lightweight for testing

### AI Providers
- **Vertex AI** (primary): Google Cloud's advanced language models
- **Rule-based** (fallback): Simple pattern matching for basic queries

### Authentication
- **Application Default Credentials** (recommended): Seamless Google Cloud integration
- **Service Account** (alternative): Explicit credential files

## 📝 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL is running
   pg_isready -h localhost -p 5432
   
   # Verify connection string
   echo $DATABASE_URL
   ```

2. **Vertex AI Authentication Error**
   ```bash
   # Re-authenticate
   gcloud auth application-default login
   
   # Verify project
   gcloud config get-value project
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

### Logs
```bash
# Enable debug logging
python main.py --debug

# Check output directory
ls -la output/
```

## 🎯 Use Cases

- **Business Intelligence**: Revenue analysis, customer insights
- **Data Exploration**: Quick database queries without SQL knowledge  
- **Report Automation**: Conversational report generation
- **Dashboard Creation**: Interactive analytics workflows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Need help?** Check the [troubleshooting section](#troubleshooting) or create an issue in the repository.