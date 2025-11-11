# test_agent_rag.py
import requests
import json
import time

# --- CONFIGURATION ---
# Use the port defined in your settings.py (8091)
BASE_URL = "http://localhost:8091/api/v1/ai" 
MOCK_TOKEN = "test-jwt-token-for-customer-123" # Must be non-null for authenticated endpoints

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def run_test_case(name, func):
    """Decorator-like runner for test functions"""
    print(f"\n[TESTING] {name}...")
    start_time = time.time()
    try:
        result = func()
        duration = time.time() - start_time
        if result and result.get("success", True):
            print(f"  ✅ PASS: {result.get('message', 'Success')} (Time: {duration:.2f}s)")
            return result
        else:
            print(f"  ❌ FAIL: {result.get('message', 'Unknown failure')}")
            return None
    except Exception as e:
        print(f"  ❌ ERROR: Test crashed - {e}")
        return None

# --- CORE ENDPOINT TESTS ---

def test_01_health_and_rag_status():
    """Test 1: Health Check and RAG System Status"""
    response_health = requests.get(f"{BASE_URL}/health", timeout=5)
    response_rag = requests.get(f"{BASE_URL}/rag/status", timeout=5)
    
    if response_health.status_code != 200:
        return {"success": False, "message": f"Health check failed (Status: {response_health.status_code})"}
    
    rag_data = response_rag.json()
    rag_available = rag_data.get("rag_available", False)
    total_vectors = rag_data.get("vector_store", {}).get("total_vectors", 0)

    return {
        "success": True, 
        "message": f"Service is UP. RAG Available: {rag_available}. Total Vectors: {total_vectors}",
        "rag_available": rag_available
    }

def test_02_ingestion_and_rag_availability(doc_id=None):
    """Test 2: Ingests a single document for RAG testing"""
    doc_content = "The warranty policy covers labor for 12 months or 12,000 miles, whichever comes first."
    payload = {
        "title": "Warranty Policy Test",
        "content": doc_content,
        "doc_type": "policy",
        "source": "test_script"
    }
    
    # Use the batch ingest endpoint for simplicity
    response = requests.post(f"{BASE_URL}/documents/batch-ingest", json=[payload], timeout=30)
    
    if response.status_code != 200:
        return {"success": False, "message": f"Ingestion failed (Status: {response.status_code}). Response: {response.text}"}

    data = response.json()
    if data.get('successful') == 1:
        return {"success": True, "message": f"Document ingested. Chunks: {data['results'][0]['chunks_created']}"}
    else:
        return {"success": False, "message": f"Ingestion failed: {data['results'][0]['error']}"}

# --- AGENT AND RAG CHAT TESTS ---

def test_03_agent_tool_routing():
    """Test 3: Checks if the Agent correctly routes to the Appointment Tool"""
    query = "Do you have any available appointments next Tuesday for an oil change?"
    payload = {"query": query, "token": MOCK_TOKEN}
    
    response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
    
    if response.status_code != 200:
        return {"success": False, "message": f"Chat failed (Status: {response.status_code}). Response: {response.text}"}

    data = response.json()
    
    # Check 1: Did the Agent execute the tool?
    tool_used = data.get("tool_executed")
    if tool_used != "Appointment_Check":
        return {"success": False, "message": f"Agent failed to route to tool. Tool executed: {tool_used}"}
        
    # Check 2: Did it return a sensible response? (Implies tool output was processed)
    if "available" not in data.get("reply", "").lower():
         return {"success": False, "message": f"Tool routed, but response is generic: {data.get('reply', '')[:50]}..."}

    return {"success": True, "message": f"Tool routed successfully. Response: {data.get('reply', '')[:50]}..."}

def test_04_rag_knowledge_retrieval():
    """Test 4: Checks if the Agent uses the RAG knowledge (Warranty Question)"""
    query = "What is the warranty period for your labor?"
    payload = {"query": query, "token": MOCK_TOKEN}
    
    response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
    
    if response.status_code != 200:
        return {"success": False, "message": f"Chat failed (Status: {response.status_code}). Response: {response.text}"}

    data = response.json()
    reply = data.get("reply", "").lower()
    
    # Check 1: Did it answer using the specific RAG data?
    if "12 months" not in reply and "12,000 miles" not in reply:
        return {"success": False, "message": f"RAG failure. Answer did not include specific warranty details: {reply[:50]}..."}

    # Check 2: Confirm no tool was executed (pure RAG/LLM response)
    if data.get("tool_executed") is not None:
         return {"success": False, "message": f"Tool was executed when it should not have been: {data.get('tool_executed')}"}

    return {"success": True, "message": f"RAG retrieval successful. Response contains specific knowledge."}

def test_05_context_filtering():
    """Test 5: Checks if the Agent ignores out-of-scope questions"""
    query = "Who was the first president of the United States?"
    payload = {"query": query, "token": MOCK_TOKEN}
    
    response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
    
    if response.status_code != 200:
        return {"success": False, "message": f"Chat failed (Status: {response.status_code}). Response: {response.text}"}

    data = response.json()
    reply = data.get("reply", "").lower()
    
    if "my knowledge is focused" not in reply and "help you with your car" not in reply:
        return {"success": False, "message": f"Filtering failed. Bot answered general knowledge: {reply[:50]}..."}

    return {"success": True, "message": "Context filtering successful."}


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    # IMPORTANT: Ensure your FastAPI service is running on port 8091 before running this script!
    print_section("STARTING AI AGENT + RAG BACKEND INTEGRATION TESTS")
    
    # 1. Check health and RAG setup
    status_result = run_test_case("1. Service Health & RAG Status", test_01_health_and_rag_status)

    if status_result and status_result.get("rag_available"):
        # 2. Test RAG Ingestion (The sample documents are in populate_knowledge_base.py)
        run_test_case("2. RAG Document Ingestion (Warranty Test)", test_02_ingestion_and_rag_availability)
        
        # 3. Test Agent Tool Routing
        run_test_case("3. Agent Tool Routing (Appointment Check)", test_03_agent_tool_routing)
        
        # 4. Test RAG Knowledge Retrieval
        run_test_case("4. RAG Knowledge Retrieval (Warranty Q)", test_04_rag_knowledge_retrieval)
        
        # 5. Test Scope Filtering
        run_test_case("5. Context Filtering (Out-of-Scope Q)", test_05_context_filtering)
    
    else:
        print("\n\n⚠️ SKIPPING RAG/AGENT TESTS: RAG system not available or Service is down.")
        print("   Please ensure Pinecone and Gemini keys are set, and FastAPI is running.")
        
    print_section("TESTS COMPLETE")