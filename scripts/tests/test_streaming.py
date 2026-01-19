import sys
sys.path.insert(0, '.')
from app import create_app
import logging
logging.basicConfig(level=logging.DEBUG)

app = create_app()

# Test with app context
with app.app_context():
    with app.test_request_context('/send_message_streaming',
                                  method='POST',
                                  json={'message': 'hello'},
                                  headers={'Content-Type': 'application/json'}):
        from flask import session, request
        
        # Set up a session
        session['session_id'] = 'test-session'
        
        # Import the route function
        from app.web.routes.analysis_routes import send_message_streaming
        
        try:
            # Call the function
            print("Calling send_message_streaming...")
            response = send_message_streaming()
            
            if response:
                print(f"Got response type: {type(response)}")
                
                # If it's a generator (streaming response)
                if hasattr(response, '__next__'):
                    print("Response is a generator/stream")
                    chunks = []
                    try:
                        for chunk in response:
                            chunks.append(chunk)
                            if len(chunks) < 5:  # Print first 5 chunks
                                print(f"Chunk: {chunk[:100] if isinstance(chunk, (str, bytes)) else chunk}")
                    except Exception as e:
                        print(f"Error iterating chunks: {e}")
                else:
                    print(f"Response: {response}")
            else:
                print("No response returned")
                
        except Exception as e:
            print(f"Error calling function: {e}")
            import traceback
            traceback.print_exc()
