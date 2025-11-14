"""
Visual representation of the LangGraph Analytics Agent workflow.
This creates a detailed flowchart showing the complete process flow.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_langgraph_visualization():
    """Create a comprehensive visualization of the LangGraph workflow."""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(16, 20))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 25)
    ax.axis('off')
    
    # Define colors for different types of components
    colors = {
        'input': '#E3F2FD',      # Light blue
        'node': '#BBDEFB',       # Medium blue
        'decision': '#FFF3E0',   # Light orange
        'ai': '#E8F5E8',         # Light green
        'database': '#F3E5F5',   # Light purple
        'output': '#FFEBEE',     # Light red
        'ui': '#E0F2F1'          # Light teal
    }
    
    # Helper function to create boxes
    def create_box(x, y, width, height, text, color, fontsize=9):
        box = FancyBboxPatch(
            (x-width/2, y-height/2), width, height,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=1
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, 
                weight='bold' if 'Node' in text else 'normal', wrap=True)
    
    # Helper function to create arrows
    def create_arrow(start_x, start_y, end_x, end_y, label=None):
        ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
        if label:
            mid_x, mid_y = (start_x + end_x) / 2, (start_y + end_y) / 2
            ax.text(mid_x + 0.2, mid_y, label, fontsize=7, color='red', weight='bold')
    
    # Title
    ax.text(5, 24, 'LangGraph Analytics Agent Workflow', 
            fontsize=18, weight='bold', ha='center')
    ax.text(5, 23.3, 'Complete End-to-End Process Flow', 
            fontsize=12, ha='center', style='italic')
    
    # 1. User Input
    create_box(2, 22, 3, 0.8, 'USER INPUT\n"show top 5 sales by amount"', colors['input'], 10)
    
    # 2. Intent Node
    create_box(2, 20.5, 2.5, 0.8, 'INTENT NODE\nAnalyze Question\n(LLM-powered)', colors['node'])
    create_arrow(2, 21.6, 2, 21.3)
    
    # 3. Decision Diamond - Clarification
    create_box(2, 19, 2, 0.8, 'DECISION\nNeed Clarification?', colors['decision'])
    create_arrow(2, 20.1, 2, 19.8)
    
    # 4a. Clarification Path (optional)
    create_box(5.5, 19, 2, 0.8, 'CLARIFICATION NODE\nAsk User Questions', colors['node'])
    create_arrow(3, 19, 4.5, 19, 'Yes')
    
    # 4b. Wait for User (optional)
    create_box(8, 19, 1.5, 0.8, 'WAIT FOR\nUSER INPUT', colors['input'])
    create_arrow(6.5, 19, 7.25, 19)
    
    # 5. Schema Lookup Node
    create_box(2, 17.5, 2.5, 0.8, 'SCHEMA LOOKUP NODE\nGet Enhanced Schema\n+ Relationships', colors['node'])
    create_arrow(2, 18.6, 2, 18.3, 'No')
    create_arrow(5.5, 18.6, 2, 18.3, 'Resolved')
    
    # 6. SQL Generation Node
    create_box(2, 16, 2.5, 0.8, 'SQL GENERATION NODE\nVertex AI + Enhanced Prompts', colors['ai'])
    create_arrow(2, 17.1, 2, 16.8)
    
    # 7. AI Processing Detail
    create_box(6, 16, 3, 1.2, 'VERTEX AI PROCESSING\n• Enhanced SQLite Prompts\n• Schema Context\n• Geographic Mapping\n• Fallback to Rule-based', colors['ai'], 8)
    create_arrow(3.25, 16, 4.5, 16)
    
    # 8. SQL Validation Node
    create_box(2, 14.5, 2.5, 0.8, 'SQL VALIDATION NODE\nSyntax & Safety Checks', colors['node'])
    create_arrow(2, 15.6, 2, 15.3)
    
    # 9. Decision - Valid SQL?
    create_box(2, 13, 2, 0.8, 'DECISION\nValid SQL?', colors['decision'])
    create_arrow(2, 14.1, 2, 13.8)
    
    # 10a. SQL Error Fix (if needed)
    create_box(5.5, 13, 2.5, 0.8, 'SQL ERROR FIX NODE\nLLM-powered Correction', colors['ai'])
    create_arrow(3, 13, 4.25, 13, 'No')
    create_arrow(5.5, 13.4, 2, 13.4, 'Retry')
    
    # 11. SQL Execution Node
    create_box(2, 11.5, 2.5, 0.8, 'SQL EXECUTION NODE\nRun Against SQLite DB', colors['database'])
    create_arrow(2, 12.6, 2, 12.3, 'Yes')
    
    # 12. Database Detail
    create_box(6, 11.5, 3, 1.2, 'SQLITE DATABASE\n• Enhanced Schema Info\n• Customers Table\n• Sales Table\n• Sample Data', colors['database'], 8)
    create_arrow(3.25, 11.5, 4.5, 11.5)
    
    # 13. Decision - Execution Success?
    create_box(2, 10, 2, 0.8, 'DECISION\nExecution Success?', colors['decision'])
    create_arrow(2, 11.1, 2, 10.8)
    
    # 14a. Error Handling
    create_arrow(3, 10, 5.5, 13, 'Error')
    
    # 15. Visualization Node
    create_box(2, 8.5, 2.5, 0.8, 'VISUALIZATION NODE\nCreate Charts & Graphs', colors['node'])
    create_arrow(2, 9.6, 2, 9.3, 'Success')
    
    # 16. Summary Node
    create_box(2, 7, 2.5, 0.8, 'SUMMARY NODE\nLLM Business Analysis', colors['ai'])
    create_arrow(2, 8.1, 2, 7.8)
    
    # 17. Final Results Assembly
    create_box(2, 5.5, 2.5, 0.8, 'RESULTS ASSEMBLY\nSQL + Data + Summary', colors['output'])
    create_arrow(2, 6.6, 2, 6.3)
    
    # 18. Streamlit UI
    create_box(2, 4, 2.5, 0.8, 'STREAMLIT UI\nChat Interface Display', colors['ui'])
    create_arrow(2, 5.1, 2, 4.8)
    
    # 19. User sees results
    create_box(2, 2.5, 3, 1.2, 'USER SEES RESULTS\n• Generated SQL\n• Data Table\n• Business Summary\n• Visualizations', colors['output'], 9)
    create_arrow(2, 3.6, 2, 3.1)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color=colors['input'], label='User Input/Output'),
        mpatches.Patch(color=colors['node'], label='Processing Nodes'),
        mpatches.Patch(color=colors['decision'], label='Decision Points'),
        mpatches.Patch(color=colors['ai'], label='AI/LLM Processing'),
        mpatches.Patch(color=colors['database'], label='Database Operations'),
        mpatches.Patch(color=colors['ui'], label='User Interface')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    # Add side annotations
    ax.text(7.5, 22, 'LANGGRAPH FEATURES:', fontsize=12, weight='bold')
    ax.text(7.5, 21.5, '• State Management', fontsize=10)
    ax.text(7.5, 21.2, '• Conditional Edges', fontsize=10)
    ax.text(7.5, 20.9, '• Error Recovery', fontsize=10)
    ax.text(7.5, 20.6, '• Retry Logic', fontsize=10)
    ax.text(7.5, 20.3, '• User Interaction', fontsize=10)
    
    ax.text(7.5, 9, 'ENHANCED FEATURES:', fontsize=12, weight='bold')
    ax.text(7.5, 8.5, '• Schema Relationship Analysis', fontsize=10)
    ax.text(7.5, 8.2, '• Geographic Mapping', fontsize=10)
    ax.text(7.5, 7.9, '• Advanced SQL Patterns', fontsize=10)
    ax.text(7.5, 7.6, '• Intelligent Fallbacks', fontsize=10)
    ax.text(7.5, 7.3, '• Context-Aware Processing', fontsize=10)
    
    # Add example flow
    ax.text(7.5, 5, 'EXAMPLE DATA FLOW:', fontsize=12, weight='bold')
    ax.text(7.5, 4.5, 'Input: "show top 5 sales by amount"', fontsize=9, style='italic')
    ax.text(7.5, 4.2, '↓', fontsize=9)
    ax.text(7.5, 3.9, 'SQL: SELECT * FROM sales', fontsize=9, family='monospace')
    ax.text(7.5, 3.6, '     ORDER BY total_amount DESC', fontsize=9, family='monospace')
    ax.text(7.5, 3.3, '     LIMIT 5', fontsize=9, family='monospace')
    ax.text(7.5, 3.0, '↓', fontsize=9)
    ax.text(7.5, 2.7, 'Results: DataFrame with 5 rows', fontsize=9, style='italic')
    ax.text(7.5, 2.4, '↓', fontsize=9)
    ax.text(7.5, 2.1, 'Summary: "Top 5 highest sales..."', fontsize=9, style='italic')
    
    plt.tight_layout()
    return fig

def create_state_flow_diagram():
    """Create a diagram showing how state flows through the system."""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Title
    ax.text(6, 7.5, 'LangGraph State Evolution', fontsize=16, weight='bold', ha='center')
    
    # State boxes showing evolution
    states = [
        {
            'x': 2, 'y': 6.5, 
            'title': 'Initial State',
            'content': '{\n  "question": "show top 5 sales",\n  "history": []\n}'
        },
        {
            'x': 6, 'y': 6.5,
            'title': 'After Schema Lookup', 
            'content': '{\n  "question": "show top 5 sales",\n  "history": [],\n  "schema": "=== DATABASE SCHEMA ===..."\n}'
        },
        {
            'x': 10, 'y': 6.5,
            'title': 'After SQL Generation',
            'content': '{\n  ...,\n  "generated_sql": "SELECT * FROM sales\\n  ORDER BY total_amount DESC\\n  LIMIT 5"\n}'
        },
        {
            'x': 2, 'y': 3.5,
            'title': 'After Validation',
            'content': '{\n  ...,\n  "validated_sql": "SELECT * FROM sales\\n  ORDER BY total_amount DESC\\n  LIMIT 5",\n  "validation_passed": true\n}'
        },
        {
            'x': 6, 'y': 3.5,
            'title': 'After Execution',
            'content': '{\n  ...,\n  "execution_result": DataFrame(5 rows),\n  "execution_error": null\n}'
        },
        {
            'x': 10, 'y': 3.5,
            'title': 'Final State',
            'content': '{\n  ...,\n  "summary": "Here are the top 5 sales...",\n  "visualization_path": "/path/to/chart.png"\n}'
        }
    ]
    
    for i, state in enumerate(states):
        # Create state box
        box = FancyBboxPatch(
            (state['x']-1.5, state['y']-1), 3, 2,
            boxstyle="round,pad=0.1",
            facecolor='lightblue',
            edgecolor='black',
            linewidth=1
        )
        ax.add_patch(box)
        
        # Add title
        ax.text(state['x'], state['y']+0.7, state['title'], 
                ha='center', va='center', fontsize=10, weight='bold')
        
        # Add content
        ax.text(state['x'], state['y']-0.2, state['content'], 
                ha='center', va='center', fontsize=8, family='monospace')
        
        # Add arrows (except for last)
        if i < len(states) - 3:  # First row
            if i < 2:
                ax.annotate('', xy=(state['x']+1.7, state['y']), 
                           xytext=(state['x']+1.5, state['y']),
                           arrowprops=dict(arrowstyle='->', lw=2))
        elif i == 2:  # Down arrow
            ax.annotate('', xy=(2, 4.5), xytext=(state['x'], state['y']-1),
                       arrowprops=dict(arrowstyle='->', lw=2))
        elif 3 <= i < 5:  # Second row
            ax.annotate('', xy=(state['x']+1.7, state['y']), 
                       xytext=(state['x']+1.5, state['y']),
                       arrowprops=dict(arrowstyle='->', lw=2))
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    # Create the main workflow visualization
    print("Creating LangGraph workflow visualization...")
    fig1 = create_langgraph_visualization()
    fig1.savefig('langgraph_workflow.png', dpi=300, bbox_inches='tight')
    print("Saved: langgraph_workflow.png")
    
    # Create the state flow diagram
    print("Creating state flow visualization...")
    fig2 = create_state_flow_diagram()
    fig2.savefig('langgraph_state_flow.png', dpi=300, bbox_inches='tight')
    print("Saved: langgraph_state_flow.png")
    
    plt.show()