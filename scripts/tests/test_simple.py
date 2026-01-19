import sys
sys.path.insert(0, '.')
import os
os.environ['FLASK_ENV'] = 'production'

from app import create_app
app = create_app()

print("Testing streaming endpoint...")
with app.test_client() as client:
    # First, establish a session
    response = client.get('/ping')
    print(f"Ping status: {response.status_code}")
    
    # Now try streaming
    response = client.post('/send_message_streaming',
                          json={'message': 'hello'},
                          headers={'Content-Type': 'application/json'})
    
    print(f"Streaming status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_data(as_text=True)
        print(f"Response length: {len(data)}")
        if data:
            print(f"First 500 chars: {data[:500]}")
        else:
            print("Empty response!")
    else:
        print(f"Error: {response.get_data(as_text=True)[:500]}")
