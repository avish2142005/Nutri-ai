import sys
sys.path.insert(0, r'd:\AI-Powered Nutrition Analyzer\backend')
from fastapi.testclient import TestClient
from index import app

client = TestClient(app)

# Test chat - ask about calories
resp = client.post('/api/chat', json={'message': 'How many calories in grilled chicken breast?'})
data = resp.json()
with open('chat_response.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {data.get('response', 'NO RESPONSE')}\n")
    f.write(f"Model: {data.get('model')}\n")
    f.write(f"Suggestions: {data.get('suggestions')}\n")
print("Written to chat_response.txt")

# Test chat - ask about carbon
resp = client.post('/api/chat', json={'message': 'What is the carbon footprint of beef?'})
data = resp.json()
with open('carbon_response.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {data.get('response', 'NO RESPONSE')}\n")
    f.write(f"Model: {data.get('model')}\n")
    f.write(f"Suggestions: {data.get('suggestions')}\n")
print("Written to carbon_response.txt")

# Test chat - general question
resp = client.post('/api/chat', json={'message': 'What are macros?'})
data = resp.json()
with open('macros_response.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {data.get('response', 'NO RESPONSE')}\n")
    f.write(f"Model: {data.get('model')}\n")
    f.write(f"Suggestions: {data.get('suggestions')}\n")
print("Written to macros_response.txt")

# Test chat - calorie question
resp = client.post('/api/chat', json={'message': 'calorie information'})
data = resp.json()
with open('calorie_response.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {data.get('response', 'NO RESPONSE')}\n")
    f.write(f"Model: {data.get('model')}\n")
    f.write(f"Suggestions: {data.get('suggestions')}\n")
print("Written to calorie_response.txt")

# Test chat - protein question
resp = client.post('/api/chat', json={'message': 'protein information'})
data = resp.json()
with open('protein_response.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Response: {data.get('response', 'NO RESPONSE')}\n")
    f.write(f"Model: {data.get('model')}\n")
    f.write(f"Suggestions: {data.get('suggestions')}\n")
print("Written to protein_response.txt")