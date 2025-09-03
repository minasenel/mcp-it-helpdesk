import asyncio
import json
import os
import sys
import subprocess
import tempfile
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
socketio = SocketIO(app, cors_allowed_origins="*")

class WebAgent:
    def __init__(self):
        self.working_directory = os.path.dirname(__file__)
    
    def process_message(self, message):
        """Process a message using the existing MCP tools"""
        try:
            # For now, let's create a simple response that shows we're working
            # and can access the MCP tools
            
            # Check if we can read the problems file
            problems_file = os.path.join(self.working_directory, "problems.txt")
            tech_experts_file = os.path.join(self.working_directory, "tech_experts.json")
            
            response_parts = []
            response_parts.append(f"I received your message: '{message}'")
            response_parts.append("I'm your IT Help Desk Agent and I'm here to help!")
            
            # Check if we can access the MCP tools
            if os.path.exists(problems_file):
                with open(problems_file, 'r', encoding='utf-8') as f:
                    problems_content = f.read().strip()
                    if problems_content:
                        response_parts.append(f"I can see there are {len(problems_content.splitlines())} existing issues in the system.")
                    else:
                        response_parts.append("I can access the problems database (currently empty).")
            
            if os.path.exists(tech_experts_file):
                with open(tech_experts_file, 'r', encoding='utf-8') as f:
                    experts_data = json.load(f)
                    response_parts.append(f"I have access to {len(experts_data)} technical experts who can help.")
            
            # Add some helpful suggestions based on the message content
            message_lower = message.lower()
            if any(word in message_lower for word in ['vpn', 'network', 'connection']):
                response_parts.append("For network/VPN issues, I can help you troubleshoot connectivity problems.")
            elif any(word in message_lower for word in ['email', 'mail', 'outlook']):
                response_parts.append("For email issues, I can help you resolve client problems and configuration issues.")
            elif any(word in message_lower for word in ['password', 'login', 'access']):
                response_parts.append("For login/password issues, I can help you reset credentials and restore access.")
            else:
                response_parts.append("I can help with various IT issues including hardware, software, network, and access problems.")
            
            response_parts.append("How can I assist you further?")
            
            return "\n\n".join(response_parts)
            
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

@socketio.on('send_message')
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
                'timestamp': time.time()
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
