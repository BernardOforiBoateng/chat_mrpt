import sys
sys.path.insert(0, '.')
from app import create_app
import requests

app = create_app()
with app.app_context():
    # Simulate what Arena does
    ollama_host = app.config.get('OLLAMA_HOST', 'localhost')
    ollama_port = app.config.get('OLLAMA_PORT', '11434')
    
    print(f"Config: OLLAMA_HOST={ollama_host}, OLLAMA_PORT={ollama_port}")
    
    # Test the exact request Arena would make
    url = f"http://{ollama_host}:{ollama_port}/v1/chat/completions"
    payload = {
        "model": "tinyllama:latest",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 10
    }
    
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"404 ERROR BODY: {response.text}")
    elif response.status_code == 200:
        print(f"SUCCESS: {response.json()['choices'][0]['message']['content']}")
