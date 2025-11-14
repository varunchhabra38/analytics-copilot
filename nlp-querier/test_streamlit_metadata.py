import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.graph import run_agent_chat

def test_streamlit_metadata_flow():
    """Test what metadata gets generated for the UI."""
    print("🧪 Testing metadata flow for Streamlit UI...")
    
    question = "What is the average transaction amount by channel for high-risk customers?"
    
    try:
        # Run the agent
        result = run_agent_chat(question, history=[])
        
        print(f"✅ Agent completed successfully!")
        print(f"📊 Result keys: {list(result.keys())}")
        
        # Check what would be stored in Streamlit metadata
        metadata = {
            "sql": result.get("sql"),
            "execution_result": result.get("execution_result"),
            "execution_error": result.get("execution_error"),
            "visualization_path": result.get("visualization_path"),
            "summary": result.get("summary")
        }
        
        print(f"\n📝 METADATA FOR STREAMLIT UI:")
        print(f"  - SQL present: {'✅' if metadata['sql'] else '❌'}")
        print(f"  - Execution result: {'✅' if metadata['execution_result'] else '❌'}")
        print(f"  - Summary present: {'✅' if metadata['summary'] else '❌'}")
        print(f"  - Summary length: {len(metadata['summary']) if metadata['summary'] else 0}")
        
        if metadata['summary']:
            print(f"\n📄 SUMMARY PREVIEW (first 200 chars):")
            print(f"'{metadata['summary'][:200]}...'")
            
        # Test the exact condition used in Streamlit
        summary_available = metadata.get("summary")
        print(f"\n🔍 STREAMLIT CONDITION TEST:")
        print(f"  - metadata.get('summary'): {'✅ TRUE' if summary_available else '❌ FALSE'}")
        print(f"  - Would show Query Explanation section: {'✅ YES' if summary_available else '❌ NO'}")
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streamlit_metadata_flow()