"""
Test script for MoatTutor API endpoints.

Script to verify that all endpoints are working correctly.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_test(name):
    """Print test name."""
    print(f"\n{YELLOW}Testing: {name}{RESET}")
    print("-" * 60)


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Print error message."""
    print(f"{RED}❌ {message}{RESET}")


def print_info(message):
    """Print info message."""
    print(f"   {message}")


def test_health():
    """Test health endpoints."""
    print_test("Health & System Endpoints")
    
    try:
        # Root endpoint
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print_success("GET / - Root endpoint")
            print_info(f"API Name: {data.get('name')}")
        else:
            print_error(f"GET / - Status: {response.status_code}")
            return False
        
        # Health check
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /health - Health check")
            print_info(f"Status: {data.get('status')}, Version: {data.get('version')}")
        else:
            print_error(f"GET /health - Status: {response.status_code}")
            return False
        
        # Metrics
        response = requests.get(f"{BASE_URL}/metrics")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /metrics - System metrics")
            print_info(f"Active Sessions: {data.get('active_sessions')}, Total Messages: {data.get('total_messages')}")
        else:
            print_error(f"GET /metrics - Status: {response.status_code}")
            return False
        
        # Ready probe
        response = requests.get(f"{BASE_URL}/ready")
        if response.status_code == 200:
            print_success("GET /ready - Readiness probe")
        else:
            print_error(f"GET /ready - Status: {response.status_code}")
            return False
        
        # Live probe
        response = requests.get(f"{BASE_URL}/live")
        if response.status_code == 200:
            print_success("GET /live - Liveness probe")
        else:
            print_error(f"GET /live - Status: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Make sure it's running on port 8000")
        print_info("Start server with: python -m uvicorn main:app --port 8000")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_companies():
    """Test company endpoints."""
    print_test("Company Endpoints")
    
    try:
        # List companies
        response = requests.get(f"{API_BASE}/companies")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/v1/companies - List companies")
            print_info(f"Found {data.get('total')} companies")
            if data.get('companies'):
                print_info(f"First company: {data['companies'][0]['name']} ({data['companies'][0]['ticker']})")
        else:
            print_error(f"GET /api/v1/companies - Status: {response.status_code}")
            return False
        
        # Get specific company
        response = requests.get(f"{API_BASE}/companies/AAPL")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/v1/companies/{ticker} - Get company")
            print_info(f"Company: {data.get('name')} ({data.get('ticker')})")
        else:
            print_error(f"GET /api/v1/companies/AAPL - Status: {response.status_code}")
            return False
        
        # Get moat analysis
        response = requests.get(f"{API_BASE}/companies/AAPL/moat")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/v1/companies/{ticker}/moat - Get moat analysis")
            print_info(f"Moat Rating: {data.get('overall_moat_rating')}")
            print_info(f"Characteristics: {len(data.get('characteristics', []))} moat characteristics")
        else:
            print_error(f"GET /api/v1/companies/AAPL/moat - Status: {response.status_code}")
            return False
        
        # Test 404 for non-existent company
        response = requests.get(f"{API_BASE}/companies/INVALID")
        if response.status_code == 404:
            print_success("GET /api/v1/companies/INVALID - 404 handling")
        else:
            print_error(f"Expected 404, got {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_sessions():
    """Test session endpoints."""
    print_test("Session Endpoints")
    
    try:
        # Create session
        response = requests.post(f"{API_BASE}/sessions")
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print_success("POST /api/v1/sessions - Create session")
            print_info(f"Session ID: {session_id}")
        else:
            print_error(f"POST /api/v1/sessions - Status: {response.status_code}")
            return False, None
        
        # Get session
        response = requests.get(f"{API_BASE}/sessions/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/v1/sessions/{session_id} - Get session")
            print_info(f"Messages: {len(data.get('messages', []))}")
        else:
            print_error(f"GET /api/v1/sessions/{session_id} - Status: {response.status_code}")
            return False, session_id
        
        # List sessions
        response = requests.get(f"{API_BASE}/sessions")
        if response.status_code == 200:
            sessions = response.json()
            print_success("GET /api/v1/sessions - List sessions")
            print_info(f"Total sessions: {len(sessions)}")
        else:
            print_error(f"GET /api/v1/sessions - Status: {response.status_code}")
            return False, session_id
        
        return True, session_id
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def test_chat(session_id=None):
    """Test chat endpoints."""
    print_test("Chat Endpoints")
    
    try:
        # Create session if not provided
        if not session_id:
            response = requests.post(f"{API_BASE}/sessions")
            if response.status_code == 200:
                session_id = response.json().get('session_id')
            else:
                print_error("Failed to create session for chat test")
                return False
        
        # Send chat message
        chat_data = {
            "query": "What are Apple's competitive advantages?",
            "session_id": session_id
        }
        response = requests.post(f"{API_BASE}/chat", json=chat_data)
        if response.status_code == 200:
            data = response.json()
            print_success("POST /api/v1/chat - Send chat message")
            print_info(f"Message ID: {data['message']['id']}")
            print_info(f"Role: {data['message']['role']}")
            content_preview = data['message']['content'][:100] + "..." if len(data['message']['content']) > 100 else data['message']['content']
            print_info(f"Content preview: {content_preview}")
            
            if data.get('parsed'):
                print_info("✅ Parsed analysis available")
                if data['parsed'].get('summary'):
                    print_info(f"Summary: {data['parsed']['summary'][:80]}...")
        else:
            print_error(f"POST /api/v1/chat - Status: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
        
        # Get chat history
        response = requests.get(f"{API_BASE}/chat/history/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/v1/chat/history/{session_id} - Get history")
            print_info(f"Total messages: {len(data.get('messages', []))}")
        else:
            print_error(f"GET /api/v1/chat/history/{session_id} - Status: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analyze():
    """Test analysis endpoints."""
    print_test("Analysis Endpoints")
    
    try:
        # Quick summary
        response = requests.get(f"{API_BASE}/analyze/AAPL/quick-summary")
        if response.status_code == 200:
            data = response.json()
            print_success("GET /api/v1/analyze/{ticker}/quick-summary - Quick summary")
            print_info(f"Ticker: {data.get('ticker')}")
            print_info(f"Moat summary: {data.get('moat_summary', '')[:80]}...")
        else:
            print_error(f"GET /api/v1/analyze/AAPL/quick-summary - Status: {response.status_code}")
            return False
        
        # Structured analysis (this might take longer if agent is invoked)
        print_info("Testing structured analysis (this may take a moment)...")
        analyze_data = {
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-02-28",
            "expertise_level": "beginner"
        }
        response = requests.post(f"{API_BASE}/analyze", json=analyze_data, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print_success("POST /api/v1/analyze - Structured analysis")
            print_info(f"Ticker: {data.get('ticker')}")
            if data.get('summary'):
                print_info(f"Summary: {data['summary'][:80]}...")
            if data.get('key_events'):
                print_info(f"Key Events: {len(data['key_events'])} events found")
        else:
            print_error(f"POST /api/v1/analyze - Status: {response.status_code}")
            print_error(f"Response: {response.text[:300]}")
            return False
        
        return True
        
    except requests.exceptions.Timeout:
        print_error("Analysis endpoint timed out (this is expected if LLM is slow)")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print(f"\n{'='*60}")
    print(f"{YELLOW}MoatTutor API Endpoint Tests{RESET}")
    print(f"{'='*60}")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test health endpoints
    results.append(("Health & System", test_health()))
    
    if not results[-1][1]:
        print(f"\n{RED}Server is not running. Please start it first.{RESET}")
        print(f"{YELLOW}Command: python -m uvicorn main:app --port 8000{RESET}")
        sys.exit(1)
    
    # Test company endpoints
    results.append(("Companies", test_companies()))
    
    # Test session endpoints
    session_success, session_id = test_sessions()
    results.append(("Sessions", session_success))
    
    # Test chat endpoints
    results.append(("Chat", test_chat(session_id)))
    
    # Test analysis endpoints
    results.append(("Analysis", test_analyze()))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"{YELLOW}Test Summary{RESET}")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"{name:20} {status}")
    
    print(f"\n{passed}/{total} test suites passed")
    
    if passed == total:
        print(f"{GREEN}🎉 All tests passed!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}⚠️  Some tests failed{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()

