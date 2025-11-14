"""
Configuration example for Google BigQuery and Vertex AI setup.

This file shows how to configure the LangGraph Analytics Agent for use with
Google Cloud services including BigQuery and Vertex AI.
"""

# Example .env file configuration
ENV_EXAMPLE = """
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
VERTEX_AI_LOCATION=us-central1

# BigQuery Configuration  
BIGQUERY_DATASET=your_dataset_name

# Optional: Alternative API keys
OPENAI_API_KEY=your_openai_key_if_needed

# Application Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
"""

# Example Python configuration
EXAMPLE_CONFIG = {
    # BigQuery Schema Tool Configuration
    "schema_tool": {
        "type": "bigquery",
        "project_id": "your-project-id",
        "credentials_path": "path/to/service-account.json",  # Optional
        "dataset_id": "your_dataset_name"  # Optional, None for all datasets
    },
    
    # Vertex AI SQL Generation Configuration
    "sql_generator": {
        "type": "vertex_ai",
        "project_id": "your-project-id", 
        "location": "us-central1",
        "model_name": "text-bison@002",
        "credentials_path": "path/to/service-account.json",  # Optional
        "temperature": 0.1
    },
    
    # BigQuery Executor Configuration
    "sql_executor": {
        "type": "bigquery",
        "project_id": "your-project-id",
        "credentials_path": "path/to/service-account.json",  # Optional
        "max_results": 10000
    }
}

# Example usage in code
USAGE_EXAMPLE = """
from agent.tools.schema_tool import create_schema_tool
from agent.tools.sql_gen_tool import create_sql_gen_tool
from agent.tools.sql_executor_tool import create_sql_executor_tool

# Create BigQuery schema tool
schema_tool = create_schema_tool(
    "bigquery",
    project_id="your-project-id",
    dataset_id="analytics"
)

# Create Vertex AI SQL generator
sql_generator = create_sql_gen_tool(
    "vertex_ai",
    project_id="your-project-id",
    location="us-central1"
)

# Create BigQuery executor
sql_executor = create_sql_executor_tool(
    "bigquery", 
    project_id="your-project-id"
)

# Get schema information
schema_info = schema_tool.get_schema()
print(schema_info)

# Generate SQL from natural language
result = sql_generator.generate_sql(
    question="Show total sales by month",
    schema=schema_info,
    history=[]
)
print(f"Generated SQL: {result['sql']}")

# Execute the query
execution_result = sql_executor.execute_query(result['sql'])
if execution_result['error']:
    print(f"Error: {execution_result['error']}")
else:
    print(f"Results: {execution_result['result']}")
"""

print("Google Cloud BigQuery and Vertex AI Configuration Guide")
print("=" * 60)
print("\n1. Environment Variables (.env file):")
print(ENV_EXAMPLE)
print("\n2. Configuration Dictionary:")
print(EXAMPLE_CONFIG)
print("\n3. Usage Example:")
print(USAGE_EXAMPLE)