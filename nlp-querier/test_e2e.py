import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.graph import run_agent_chat

def test_end_to_end():
    """Test the complete end-to-end flow including summary generation."""
    print("🧪 Testing end-to-end query processing...")
    
    question = "What is the average transaction amount by channel?"
    
    try:
        # Run the complete agent workflow
        result = run_agent_chat(question, history=[])
        
        print(f"✅ Agent completed successfully!")
        print(f"📊 Result keys: {list(result.keys())}")
        
        if result.get("summary"):
            print(f"📝 Summary length: {len(result['summary'])} characters")
            print("📝 Summary content:")
            print("-" * 60)
            print(result["summary"])
            print("-" * 60)
        else:
            print("❌ No summary in result")
            
        if result.get("sql"):
            print(f"🔍 SQL generated: {result['sql'][:100]}...")
            
        if result.get("execution_result"):
            print(f"📈 Execution result type: {type(result['execution_result'])}")
            
    except Exception as e:
        print(f"❌ Error in end-to-end test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_end_to_end()