import sys
import httpx
import json

BASE_URL = "https://autonomous-agent-backend-production.up.railway.app"

def run_test():
    print(f"Connecting to live backend: {BASE_URL}")

    # 1. Sign in or sign up
    client = httpx.Client(base_url=BASE_URL, timeout=120.0)
    email = "test_operator_live@example.com"
    password = "LivePassword123!"

    print("Authenticating...")
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    if login_res.status_code != 200:
        print("Creating live test operator account...")
        signup_res = client.post("/auth/signup", json={"name": "Live Operator", "email": email, "password": password})
        if signup_res.status_code not in [200, 201]:
            print(f"Signup failed: {signup_res.status_code} {signup_res.text}")
            sys.exit(1)
        login_res = client.post("/auth/login", json={"email": email, "password": password})

    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Authentication successful!")

    # Test 1: find_customer
    print("\n=======================================================")
    print("TEST 1: find_customer")
    print("User Prompt: 'Can you find customer Alice and give me her details?'")
    r1 = client.post("/conversations", headers=headers, json={"message": "Can you find customer Alice and give me her details?"})
    if r1.status_code != 201:
        print(f"Failed: {r1.status_code} {r1.text}")
        sys.exit(1)
    d1 = r1.json()
    conv_id = d1["conversation_id"]
    print(f"Conversation ID: {conv_id}")
    print(f"Agent Summary:\n{d1['agent_response']['content']}")
    print(f"Tool Calls ({len(d1['tool_calls'])}):")
    for tc in d1["tool_calls"]:
        print(f"  Tool: {tc['tool_name']}")
        print(f"  Input: {json.dumps(tc['tool_input'])}")
        print(f"  Output: {json.dumps(tc['tool_output'])}")

    # Test 2: get_order
    print("\n=======================================================")
    print("TEST 2: get_order")
    print("User Prompt: 'What are the details and status of order ord-101?'")
    r2 = client.post(f"/conversations/{conv_id}/messages", headers=headers, json={"message": "What are the details and status of order ord-101?"})
    if r2.status_code != 200:
        print(f"Failed: {r2.status_code} {r2.text}")
        sys.exit(1)
    d2 = r2.json()
    print(f"Agent Summary:\n{d2['agent_response']['content']}")
    print(f"Tool Calls ({len(d2['tool_calls'])}):")
    for tc in d2["tool_calls"]:
        print(f"  Tool: {tc['tool_name']}")
        print(f"  Input: {json.dumps(tc['tool_input'])}")
        print(f"  Output: {json.dumps(tc['tool_output'])}")

    # Test 3: get_order_history
    print("\n=======================================================")
    print("TEST 3: get_order_history")
    print("User Prompt: 'Show me the order history for customer c001-alice-smith.'")
    r3 = client.post(f"/conversations/{conv_id}/messages", headers=headers, json={"message": "Show me the order history for customer c001-alice-smith."})
    if r3.status_code != 200:
        print(f"Failed: {r3.status_code} {r3.text}")
        sys.exit(1)
    d3 = r3.json()
    print(f"Agent Summary:\n{d3['agent_response']['content']}")
    print(f"Tool Calls ({len(d3['tool_calls'])}):")
    for tc in d3["tool_calls"]:
        print(f"  Tool: {tc['tool_name']}")
        print(f"  Input: {json.dumps(tc['tool_input'])}")
        print(f"  Output: {json.dumps(tc['tool_output'])}")

    # Test 4: calculate_balance
    print("\n=======================================================")
    print("TEST 4: calculate_balance")
    print("User Prompt: 'Calculate the balance and account standing for customer c001-alice-smith.'")
    r4 = client.post(f"/conversations/{conv_id}/messages", headers=headers, json={"message": "Calculate the balance and account standing for customer c001-alice-smith."})
    if r4.status_code != 200:
        print(f"Failed: {r4.status_code} {r4.text}")
        sys.exit(1)
    d4 = r4.json()
    print(f"Agent Summary:\n{d4['agent_response']['content']}")
    print(f"Tool Calls ({len(d4['tool_calls'])}):")
    for tc in d4["tool_calls"]:
        print(f"  Tool: {tc['tool_name']}")
        print(f"  Input: {json.dumps(tc['tool_input'])}")
        print(f"  Output: {json.dumps(tc['tool_output'])}")
    for tc in d4["tool_calls"]:
        print(f"  Tool: {tc['tool_name']}")
        print(f"  Input: {json.dumps(tc['tool_input'])}")
        print(f"  Output: {json.dumps(tc['tool_output'])}")

    print("\n=======================================================")
    print("ALL 4 LIVE TOOL TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
