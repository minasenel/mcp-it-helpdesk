import asyncio
import json
import os
import sys
import subprocess
import tempfile
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import queue

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
socketio = SocketIO(app, cors_allowed_origins="*")

class WebAgent:
    def __init__(self):
        self.working_directory = os.path.dirname(__file__)
    
    def process_message(self, message): # This function processes a message through the FastAgent CLI
        """Process a message through the FastAgent CLI"""
        try:
            # Create a temporary file for the message
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(message)
                temp_input_path = temp_file.name
            
            try:
                # Use subprocess to call the agent with the message
                # We'll use a simple approach: write message to temp file and read response
                cmd = ["python", "-c", f"""
import sys
import os
sys.path.insert(0, '{self.working_directory}')

# Read the message from temp file
with open('{temp_input_path}', 'r') as f:
    user_message = f.read().strip()

# Import and use the FastAgent
try:
    from mcp_agent.core.fastagent import FastAgent
    import asyncio
    
    async def process_with_agent():
        fast = FastAgent("Web-based IT Help Desk Agent")
        
        @fast.agent(instruction="You are a helpful IT support agent. You can help with technical issues, troubleshoot problems, and provide solutions. Be friendly and professional. You have access to MCP tools for managing IT issues.")
        async def web_agent():
            async with fast.run() as agent:
                # Send the user message to the agent
                response = await agent.send_message(user_message)
                return response
        
        return await process_with_agent()
    
    # Run the async function
    result = asyncio.run(process_with_agent())
    print(result)
    
except Exception as e:
    print(f"Error: {{str(e)}}")
    print(f"I received your message: '{{user_message}}'. I'm an IT support agent and I'm here to help you with technical issues. How can I assist you today?")
"""]
                
                # Run the command and capture output
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.working_directory)
                
                if result.returncode == 0:
                    response = result.stdout.strip()
                    if response:
                        return response
                    else:
                        return f"I received your message: '{message}'. I'm an IT support agent and I'm here to help you with technical issues. How can I assist you today?"
                else:
                    error_msg = result.stderr.strip()
                    return f"I received your message: '{message}'. I'm an IT support agent and I'm here to help you with technical issues. How can I assist you today? (Note: {error_msg})"
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_input_path)
                except:
                    pass
            
        except Exception as e:
            return f"Error processing message: {str(e)}"

# Initialize the web agent
web_agent = WebAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return "Web agent is working! Go to <a href='/'>the main page</a>"

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to IT Help Desk Agent'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('send_message') # This function handles the message sent by the client
def handle_message(data):
    message = data.get('message', '')
    if not message:
        emit('error', {'message': 'Empty message received'})
        return
    
    # Process message in a separate thread to avoid blocking
    def process_in_thread():
        try:
            # Process the message
            response = web_agent.process_message(message)
            
            # Send response back to client
            socketio.emit('agent_response', {
                'message': response,
                'timestamp': asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
            })
            
        except Exception as e:
            socketio.emit('error', {'message': f'Error: {str(e)}'})
    
    # Start processing in a separate thread
    thread = threading.Thread(target=process_in_thread)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("Starting Web-based IT Help Desk Agent...")
    print("Open your browser and go to: http://localhost:5001")
    socketio.run(app, debug=True, host='127.0.0.1', port=5001)
