You are GitHub Copilot. Follow these instructions across the repository.

Your job is to build a production-ready, modular, extensible LangGraph-based

Analytics Agent that supports:

✅ Natural language → SQL → validation → execution → visualization → summary  

✅ Conversational chat interface (multi-turn, follow-up questions)  

✅ Agentic flow with tool-based nodes  

✅ Clarification loops via LangGraph "wait for user" states  

✅ Context retention via conversation memory  

✅ Streamlit or FastAPI chat front-end  

✅ Clean, tested, maintainable modular code  

================================================================

===================== HIGH-LEVEL OBJECTIVE =====================

================================================================

Build a single-agent, multi-tool analytics system using LangGraph that:

1. Accepts user natural-language questions in a chat interface

2. Maintains full multi-turn conversation context

3. Supports follow-up queries ("filter previous result by EMEA", etc.)

4. Automatically looks up schema, generates SQL, validates, executes, retries

5. Builds visualizations and summaries

6. Uses LangGraph for branching + retries + user clarification

7. Returns a chat-style JSON response for UI rendering

This should function similarly to Databricks Genie or ChatGPT data analysis.

================================================================

======================== PROJECT STRUCTURE ======================

================================================================

project_root/

    main.py

    requirements.txt

    agent/

        __init__.py

        state.py              # holds conversation + agent state

        graph.py              # defines the LangGraph workflow

        nodes/

            __init__.py

            intent.py

            lookup_schema.py

            generate_sql.py

            validate_sql.py

            execute_sql.py

            fix_sql_error.py

            clarification.py   # ask user questions

            visualize.py

            summarize.py

        tools/

            __init__.py

            schema_tool.py

            sql_gen_tool.py

            sql_validator_tool.py

            sql_executor_tool.py

            error_fix_tool.py

            viz_tool.py

            summary_tool.py

            summary_prompt.txt

    utils/

        db.py

        logging.py

        exceptions.py

    ui/

        streamlit_app.py      # or fastapi_chat.py

    output/

        (generated charts, logs, etc.)

================================================================

======================= CHAT REQUIREMENTS =======================

================================================================

The system must implement **three levels of chat**:

-------------------------------------------------------------

1) CHAT UI LAYER

-------------------------------------------------------------

- Build a Streamlit chat interface OR a FastAPI chat endpoint.

- Should support:

    - user messages

    - assistant messages

    - visualization display

    - conversation token persistence

Example UI behavior:

- User asks: "Show revenue by month"

- Agent responds with SQL + chart + summary

- User asks: "Filter by EMEA"

- Agent uses previous SQL + conversation context to refine query.

streamlit_app.py example:
 
-------------------------------------------------------------

2) CONVERSATION MEMORY (STATE)

-------------------------------------------------------------

Add conversation memory to AgentState:

class AgentState(TypedDict):

    question: str

    history: list[dict]                 # {role, content}

    schema: str | None

    generated_sql: str | None

    validated_sql: str | None

    execution_result: pd.DataFrame | None

    execution_error: str | None

    visualization_path: str | None

    summary: str | None

    last_sql: str | None

    clarification_needed: bool

    clarification_question: str | None

    user_clarification_response: str | None

- All nodes must update the state immutably.

- sql_gen_tool must use the full conversation history to interpret follow-ups.

- Summaries should append messages to history.

-------------------------------------------------------------

3) CHAT-AS-PART-OF-LANGGRAPH (AGENT WORKFLOW)

-------------------------------------------------------------

Implement LangGraph "wait for user" node for clarifications.

Example flow:

intent → lookup_schema → generate_sql  

→ validate_sql → execute_sql  

→ (if error) fix_sql_error → validate_sql  

→ visualize → summarize → END

**BUT** with branching:

- If question ambiguous:

    → clarification node

        → wait for user input

        → next run, inject response → continue

clarification.py node example:
 
Graph should use:

- Conditional edges

- Retry loops

- User-in-the-loop waiting

================================================================

===================== NODE REQUIREMENTS =========================

================================================================

Implement these nodes:

1. intent.py

    - Detect ambiguity (multiple date columns, etc.)

    - If ambiguous → set state["clarification_needed"] = True

2. clarification.py

    - Emit a clarification question and halt.

3. lookup_schema.py

    - Use SchemaLookupTool → build schema text.

4. generate_sql.py

    - Use SQLGenTool

    - Use schema + conversation history

    - Must output JSON: {"sql": "...", "explain": "..."}

5. validate_sql.py

    - Use SQLValidatorTool to enforce safety rules.

6. execute_sql.py

    - Use SQLExecutorTool

    - Capture df OR error.

7. fix_sql_error.py

    - Use SQLErrorFixTool

    - Retry loop, max_retries = 3

8. visualize.py

    - Use VizTool → saves plot to output/

9. summarize.py

    - Use SummaryTool

    - Append to conversation history.

================================================================

====================== TOOL REQUIREMENTS ========================

================================================================

Tools must be modular and testable.

Tool list:

- SchemaLookupTool

- SQLGenTool

- SQLValidatorTool

- SQLExecutorTool

- SQLErrorFixTool

- VizTool

- SummaryTool

Place in agent/tools/.

================================================================

==================== LANGGRAPH WORKFLOW ========================

================================================================

In agent/graph.py:

- Build a LangGraph graph:

    - nodes for each step

    - conditional edges

    - retry logic

    - clarification support

    - final output returned as dict

- Expose a function:

run_agent_chat(question: str, history: list) → dict:

    - populate initial AgentState

    - run LangGraph

    - return:

        {

            "sql": ...,

            "summary": ...,

            "visualization_path": ...,

            "history": updated_history

        }

================================================================

==================== CODING & ENGINEERING RULES ================

================================================================

Copilot must always:

✅ Use type hints  

✅ Add docstrings  

✅ Keep modules small & clean  

✅ Avoid monolithic files  

✅ Avoid hardcoding model names  

✅ Use dependency injection for DB engine  

✅ Write testable, pure functions when possible  

✅ Add logging for each node transition  

✅ Maintain immutable state updates  

================================================================

=========================== BEGIN ===============================

================================================================

Start by generating the folder structure and then scaffold:

- agent/state.py  

- agent/nodes/intent.py  

- agent/tools/schema_tool.py  

- agent/graph.py  

Then proceed to implement remaining modules.
 