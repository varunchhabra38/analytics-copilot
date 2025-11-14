# LangGraph Analytics Agent - Google Cloud Edition

A production-ready analytics agent powered by **Google BigQuery** and **Vertex AI** that converts natural language questions into SQL queries, executes them, and provides intelligent insights.

## 🌟 Google Cloud Features

- **🔍 BigQuery Integration**: Native support for Google BigQuery with optimized SQL generation
- **🤖 Vertex AI Power**: Uses Google's Vertex AI language models for intelligent SQL generation
- **🔐 Seamless Authentication**: Works with Application Default Credentials or service accounts
- **📊 BigQuery-Optimized**: Leverages BigQuery's unique features (arrays, structs, columnar storage)
- **💰 Cost Conscious**: Built-in query cost management and result limiting

## 🚀 Quick Start with Google Cloud

### Prerequisites

1. **Google Cloud Project** with BigQuery and Vertex AI APIs enabled
2. **Authentication** set up (service account or Application Default Credentials)
3. **Python 3.8+**

### Setup Steps

1. **Clone and install**:
```bash
git clone <repository-url>
cd nlp-querier
pip install -r requirements.txt
```

2. **Configure Google Cloud authentication**:

**Option A: Service Account (Recommended for production)**
```bash
# Download service account key from Google Cloud Console
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

**Option B: Application Default Credentials (For development)**
```bash
gcloud auth application-default login
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your values:
```

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET=your_dataset_name
VERTEX_AI_LOCATION=us-central1
```

4. **Run the application**:
```bash
# Streamlit UI
python main.py streamlit

# CLI for testing
python main.py cli
```

## 🔧 Google Cloud Configuration

### BigQuery Setup

Your `.env` file for BigQuery:
```bash
GOOGLE_CLOUD_PROJECT=my-analytics-project
BIGQUERY_DATASET=sales_data
GOOGLE_APPLICATION_CREDENTIALS=./gcp-key.json  # Optional
```

### Vertex AI Configuration

```bash
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=text-bison@002
```

### Programmatic Configuration

```python
from agent.tools.schema_tool import create_schema_tool
from agent.tools.sql_gen_tool import create_sql_gen_tool
from agent.tools.sql_executor_tool import create_sql_executor_tool

# BigQuery schema discovery
schema_tool = create_schema_tool(
    "bigquery",
    project_id="your-project-id",
    dataset_id="analytics_data"
)

# Vertex AI SQL generation
sql_generator = create_sql_gen_tool(
    "vertex_ai",
    project_id="your-project-id",
    location="us-central1",
    model_name="text-bison@002"
)

# BigQuery query execution
sql_executor = create_sql_executor_tool(
    "bigquery",
    project_id="your-project-id",
    max_results=10000
)
```

## 💬 BigQuery-Optimized Queries

The agent generates BigQuery-specific SQL with advanced features:

### Example Interactions

**Natural Language**: "Show me monthly revenue trends for 2023"

**Generated BigQuery SQL**:
```sql
SELECT 
  EXTRACT(MONTH FROM order_date) as month,
  EXTRACT(YEAR FROM order_date) as year,
  SUM(total_amount) as monthly_revenue
FROM `project.dataset.orders`
WHERE EXTRACT(YEAR FROM order_date) = 2023
GROUP BY month, year
ORDER BY month
```

**Natural Language**: "What are the top 5 products by sales in EMEA?"

**Generated BigQuery SQL**:
```sql
WITH regional_sales AS (
  SELECT 
    p.product_name,
    SUM(o.quantity * o.unit_price) as total_sales
  FROM `project.dataset.orders` o
  JOIN `project.dataset.products` p ON o.product_id = p.product_id
  WHERE o.region = 'EMEA'
  GROUP BY p.product_name
)
SELECT 
  product_name,
  total_sales
FROM regional_sales
ORDER BY total_sales DESC
LIMIT 5
```

## 🛡️ Security & Cost Management

### Built-in Safety Features

- **Query Validation**: Prevents modification queries (DROP, DELETE, UPDATE)
- **Cost Limits**: Configurable maximum bytes billed per query
- **Result Limits**: Automatic LIMIT clauses to prevent large result sets
- **SQL Injection Protection**: Parameterized queries where applicable

### Cost Controls

```python
# Configure cost controls in BigQuery executor
sql_executor = create_sql_executor_tool(
    "bigquery",
    project_id="your-project-id",
    max_results=10000,  # Limit rows returned
    max_bytes_billed=1024*1024*1024  # 1 GB limit
)
```

## 🎨 Advanced BigQuery Features

The agent leverages BigQuery's unique capabilities:

- **Array and Struct handling**: Automatically generates UNNEST operations
- **Date/Time functions**: Uses BigQuery's rich temporal functions
- **Window functions**: Generates advanced analytics queries
- **Geographic functions**: Supports GIS queries when geodata is present
- **ML integration**: Can generate BigQuery ML queries for predictions

## 📊 Streamlit UI Features

### BigQuery-Specific UI Elements

- **Query Cost Display**: Shows bytes processed and billed
- **Performance Metrics**: Displays query execution time and cache hits
- **Result Export**: Download BigQuery results as CSV/JSON
- **Query History**: Track and rerun successful queries

### Sample UI Flow

1. **User Input**: "Show customer acquisition trends"
2. **Agent Analysis**: Detects ambiguity, asks for time period
3. **User Clarification**: "Last 12 months by quarter"
4. **Schema Discovery**: Automatically finds customer and date tables
5. **SQL Generation**: Creates optimized BigQuery SQL with Vertex AI
6. **Query Execution**: Runs query with cost/performance monitoring
7. **Visualization**: Generates interactive chart from results
8. **Summary**: Provides natural language insights

## 🔍 Troubleshooting

### Common Issues

**Authentication Error**:
```bash
# Verify credentials
gcloud auth list
gcloud config set project YOUR_PROJECT_ID
```

**BigQuery Permission Error**:
```bash
# Ensure your account has BigQuery User and Data Viewer roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@gmail.com" \
  --role="roles/bigquery.user"
```

**Vertex AI Not Available**:
```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

### Performance Optimization

1. **Use partitioned tables** for time-based queries
2. **Cluster tables** by frequently filtered columns  
3. **Use approximate aggregation** functions for large datasets
4. **Leverage materialized views** for complex repeated queries

## 📈 Monitoring and Analytics

### Query Performance Tracking

The system automatically tracks:
- Query execution time
- Bytes processed and billed
- Cache hit rates
- Error rates and types

### Usage Analytics

Monitor your usage through:
- BigQuery console for detailed query logs
- Google Cloud Monitoring for cost tracking
- Application logs for user interaction patterns

## 🚀 Deployment Options

### Cloud Run Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

ENV GOOGLE_CLOUD_PROJECT=your-project-id
ENV PORT=8080

CMD python main.py fastapi --host=0.0.0.0 --port=$PORT
```

### Vertex AI Workbench

Deploy directly in Google Cloud's managed Jupyter environment with pre-configured access to BigQuery and Vertex AI.

---

**Built with ❤️ for Google Cloud Platform**

*Powered by BigQuery's lightning-fast analytics and Vertex AI's intelligent language understanding*