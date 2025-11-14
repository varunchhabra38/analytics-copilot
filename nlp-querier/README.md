# nlp-querier

## Overview
The NLP Querier project is a modular, extensible analytics agent that transforms natural language queries into SQL commands, executes them, and provides visualizations and summaries. It utilizes LangGraph for managing workflows and supports a conversational chat interface for user interaction.

## Features
- **Natural Language Processing**: Converts user queries into SQL commands.
- **Multi-Turn Conversations**: Maintains context across multiple interactions.
- **Schema Lookup**: Automatically retrieves database schema information.
- **SQL Generation and Validation**: Generates SQL queries and validates them for safety.
- **Execution and Error Handling**: Executes SQL commands and handles errors with retries.
- **Visualization**: Creates visual representations of query results.
- **Summarization**: Provides summaries of the conversation and results.

## Project Structure
```
nlp-querier
├── main.py                  # Entry point for the application
├── requirements.txt         # Project dependencies
├── agent                    # Contains the core agent logic
│   ├── __init__.py
│   ├── state.py             # Holds conversation and agent state
│   ├── graph.py             # Defines the LangGraph workflow
│   ├── nodes                # Contains nodes for various operations
│   └── tools                # Contains tools for schema lookup, SQL generation, etc.
├── utils                    # Utility functions and classes
│   ├── __init__.py
│   ├── db.py                # Database connection logic
│   ├── logging.py           # Logging functionality
│   └── exceptions.py        # Custom exceptions
├── ui                       # User interface components
│   └── streamlit_app.py     # Streamlit chat interface
├── output                   # Directory for generated outputs
│   └── .gitkeep             # Keeps the output directory in version control
└── README.md                # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd nlp-querier
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
Run the application using:
```
python main.py
```
This will start the chat interface where users can input their queries.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.