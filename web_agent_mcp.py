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
        """Process a message using the MCP tools"""
        try:
            # Create a temporary script that will use the MCP tools
            # Escape the message to prevent issues with quotes
            escaped_message = message.replace('"', '\\"').replace("'", "\\'")
            script_content = '''
import sys
import os
sys.path.insert(0, "{working_dir}")

# Import the MCP tools
from main import ai_try_solve, assign_expert, add_issue, process_issues
import json

user_message = """{user_msg}"""

# Try to classify the issue and solve it
try:
    # First, try to solve with AI
    print("🤖 AI is analyzing your issue...")
    
    # First, check if this is actually a problem report or just conversation
    message_lower = user_message.lower().strip()
    
    # Greeting and conversation patterns (not problems)
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you', 'bye', 'goodbye']
    questions = ['how are you', 'what can you do', 'help me', 'what is this', 'who are you']
    
    # Check if it's just a greeting or question
    # Only treat as greeting if it's a simple greeting without technical keywords
    is_simple_greeting = (any(greeting in message_lower for greeting in greetings) and 
                         len(message_lower.split()) <= 3 and
                         not any(tech_word in message_lower for tech_word in ['vpn', 'network', 'wifi', 'email', 'password', 'login', 'crash', 'error', 'broken', 'not working', 'problem', 'issue', 'help', 'fix', 'troubleshoot']))
    
    if is_simple_greeting:
        print("👋 Detected greeting/conversation, not a technical problem")
        response = """👋 Hello! I'm your IT Help Desk Agent. 

I'm here to help you with technical issues like:
• **Hardware problems** (computer, printer, mouse, keyboard issues)
• **Software issues** (applications not working, crashes, errors)
• **Network problems** (VPN, WiFi, internet connectivity)
• **Access issues** (login problems, password resets, account issues)

To report a technical problem, please describe:
- What exactly is not working?
- When did it start?
- What error messages do you see?

**Example:** "My VPN keeps disconnecting every 10 minutes and I can't access company servers."

How can I help you with a technical issue today?"""
        print(response)
        exit(0)
    
    # Check if it's a follow-up request for expert assistance
    if any(phrase in message_lower for phrase in [
        'need further assistance', 'assign me with', 'human expert', 'assign expert', 'escalate', 'transfer to',
        'assign me', 'assign an expert', 'assign me an expert', 'assign to human', 'connect me to human',
        'talk to human', 'contact an expert', 'assing expert', 'assing human', 'assing me'
    ]):
        print("🔄 Detected expert assignment request")
        
        # Try to determine the issue category from the conversation context
        # For now, we'll use a general approach and let the user specify
        issue_category = "general"
        issue_subcategory = "general"
        
        # Load experts and find the best match
        try:
            import json
            experts_file = os.path.join("{working_dir}", "tech_experts.json")
            with open(experts_file, 'r', encoding='utf-8') as f:
                experts = json.load(f)
            
            # Find available experts
            available_experts = [expert for expert in experts if expert.get('availability', True)]
            
            if available_experts:
                # For now, assign the first available expert
                # In a real system, you'd match based on expertise
                assigned_expert = available_experts[0]
                expert_name = assigned_expert.get('name', 'Unknown Expert')
                expert_contact = assigned_expert.get('contact', 'contact@example.com')
                expert_skills = ', '.join(assigned_expert.get('expertise', []))
                
                response = """🔄 **Expert Assignment Complete**

**Assigned Expert:** """ + expert_name + """

**Contact Information:** """ + expert_contact + """

**Expertise Areas:** """ + expert_skills + """

**Next Steps:**
• Contact the expert directly using the email above
• Mention your issue details and reference any issue ID you received
• The expert will respond within 24 hours

**Your Issue:** """ + user_message + """

Is there anything else I can help you with?"""
            else:
                response = """🔄 **Expert Assignment Request**

Unfortunately, no experts are currently available. 

**Alternative Options:**
• Try the AI solution provided earlier
• Submit a detailed ticket through our support portal
• Check back in a few hours for expert availability

**Your Issue:** """ + user_message + """

Is there anything else I can help you with?"""
                
        except Exception as e:
            response = """🔄 **Expert Assignment Request**

I understand you need further assistance with your technical issue.

**Your Issue:** """ + user_message + """

**Next Steps:**
• I'll assign you to a human expert who specializes in your issue type
• The expert will contact you within 24 hours
• You'll receive an email with expert contact details

**Current Status:** Your issue has been logged and is being processed.

Is there anything else I can help you with while you wait for the expert?"""
        
        print(response)
        exit(0)
    
    # Check if it's a general question about capabilities
    if any(question in message_lower for question in questions):
        print("❓ Detected capability question")
        response = """🤖 I'm an IT Help Desk Agent with access to:

**Available Tools:**
• AI-powered problem analysis
• Expert assignment system  
• Issue tracking and logging
• Technical problem classification

**I can help with:**
• Hardware issues (computers, printers, peripherals)
• Software problems (applications, crashes, errors)
• Network connectivity (VPN, WiFi, internet)
• Access and authentication issues

**To get help:** Describe your specific technical problem with details about what's not working, when it started, and any error messages you see.

What technical issue can I help you with?"""
        print(response)
        exit(0)
    
    # Now analyze for actual technical problems
    print("🔍 Analyzing for technical problem...")
    
    # Determine category and subcategory based on keywords
    # Network issues
    if any(word in message_lower for word in ['vpn', 'network', 'wifi', 'internet', 'connection', 'disconnect', 'connectivity', 'dropping', 'reconnecting', 'connection lost', 'anyconnect']):
        category = "network"
        if 'vpn' in message_lower or 'anyconnect' in message_lower:
            subcategory = "vpn"
        elif 'wifi' in message_lower or 'wi-fi' in message_lower:
            subcategory = "wifi"
        else:
            subcategory = "network"
    # Email issues
    elif any(word in message_lower for word in ['email', 'mail', 'outlook', 'gmail', 'thunderbird', 'smtp', 'pop3']):
        category = "software"
        subcategory = "email"
    # Login/Access issues
    elif any(word in message_lower for word in ['password', 'login', 'access', 'account', 'credential', 'authentication', 'sign in', 'log in']):
        category = "software"
        subcategory = "login"
    # Hardware issues
    elif any(word in message_lower for word in ['hardware', 'computer', 'laptop', 'printer', 'mouse', 'keyboard', 'monitor', 'fan', 'battery', 'screen', 'display']):
        category = "hardware"
        subcategory = "hardware"
    # Software issues
    elif any(word in message_lower for word in ['crash', 'error', 'bug', 'not working', 'broken', 'freeze', 'slow', 'application', 'software', 'program', 'app']):
        category = "software"
        subcategory = "general"
    # If it contains problem indicators but unclear category
    elif any(word in message_lower for word in ['problem', 'issue', 'trouble', 'help', 'fix', 'broken', 'not working', 'cannot', 'unable']):
        category = "software"
        subcategory = "general"
    else:
        # If we can't clearly classify, ask for more details
        print("❓ Unclear problem description, asking for clarification")
        response = """❓ I need more details to help you effectively.

Your message: \"""" + user_message + """\"

**Please provide more information:**
• What exactly is not working?
• What were you trying to do when the problem occurred?
• Do you see any error messages?
• When did this problem start?

**Examples of good problem reports:**
• "My VPN keeps disconnecting every 10 minutes"
• "Outlook crashes when I try to send large attachments"
• "I can't log into my work account, getting 'invalid credentials' error"
• "My laptop fan is making loud noise and running slowly"

Please describe your technical issue with more details so I can help you properly."""
        print(response)
        exit(0)
    
    # Determine priority
    if any(word in message_lower for word in ['urgent', 'critical', 'emergency', 'down', 'broken']):
        priority = "high"
    elif any(word in message_lower for word in ['important', 'soon', 'asap']):
        priority = "medium"
    else:
        priority = "low"
    
    print("📋 Issue classified as: " + category + "/" + subcategory + " (" + priority + " priority)")
    
    # Try AI solution first
    ai_solution = ai_try_solve(user_message, category, subcategory, priority)
    
    if "Çözüm önerisi bulunamadı" not in ai_solution:
        print("✅ AI found a solution!")
        print("💡 Solution: " + ai_solution)
        
        # Create the issue in the system
        issue_id = add_issue("WEB_USER", user_message, category, subcategory, priority)
        print("📝 Issue logged: " + issue_id)
        
        response = """✅ **AI Solution Found!**

**Issue:** """ + user_message + """
**Category:** """ + category + "/" + subcategory + """
**Priority:** """ + priority + """

**Solution:**
""" + ai_solution + """

**Issue ID:** """ + issue_id + """

Is this solution helpful? If you need further assistance, I can assign you to a human expert."""
        
    else:
        print("🤔 AI couldn't solve automatically, assigning expert...")
        
        # Create the issue in the system first
        issue_id = add_issue("WEB_USER", user_message, category, subcategory, priority)
        
        # Load experts and find the best match
        try:
            import json
            experts_file = os.path.join("{working_dir}", "tech_experts.json")
            with open(experts_file, 'r', encoding='utf-8') as f:
                experts = json.load(f)
            
            # Find experts with matching expertise
            matching_experts = []
            for expert in experts:
                if expert.get('availability', True):
                    expertise = expert.get('expertise', [])
                    if (category in expertise or 
                        subcategory in expertise or 
                        any(skill in expertise for skill in [category, subcategory])):
                        matching_experts.append(expert)
            
            if matching_experts:
                assigned_expert = matching_experts[0]
                expert_name = assigned_expert.get('name', 'Unknown Expert')
                expert_contact = assigned_expert.get('contact', 'contact@example.com')
                expert_skills = ', '.join(assigned_expert.get('expertise', []))
                
                response = """🤖 **AI Analysis Complete - Expert Assigned**

**Issue:** """ + user_message + """
**Category:** """ + category + "/" + subcategory + """
**Priority:** """ + priority + """

**AI Analysis:** I couldn't find an automated solution for this issue.

**Assigned Expert:** """ + expert_name + """
**Contact:** """ + expert_contact + """
**Expertise:** """ + expert_skills + """

**Issue ID:** """ + issue_id + """

**Next Steps:**
• Contact the expert directly using the email above
• Mention your issue details and reference the issue ID
• The expert will respond within 24 hours

A human expert will help you resolve this issue."""
            else:
                # Fallback to generic expert assignment
                expert_assignment = assign_expert(user_message)
                response = """🤖 **AI Analysis Complete**

**Issue:** """ + user_message + """
**Category:** """ + category + "/" + subcategory + """
**Priority:** """ + priority + """

**AI Analysis:** I couldn't find an automated solution for this issue.

**Expert Assignment:** """ + expert_assignment + """

**Issue ID:** """ + issue_id + """

A human expert will be in touch with you soon to resolve this issue."""
                
        except Exception as e:
            # Fallback to generic expert assignment
            expert_assignment = assign_expert(user_message)
            response = """🤖 **AI Analysis Complete**

**Issue:** """ + user_message + """
**Category:** """ + category + "/" + subcategory + """
**Priority:** """ + priority + """

**AI Analysis:** I couldn't find an automated solution for this issue.

**Expert Assignment:** """ + expert_assignment + """

**Issue ID:** """ + issue_id + """

A human expert will be in touch with you soon to resolve this issue."""
    
    print(response)
    
except Exception as e:
    print("❌ Error: " + str(e))
    print("I received your message: '" + user_message + "'. I'm your IT Help Desk Agent. How can I help you today?")
'''
            
            # Format the script content with the actual values
            formatted_script = script_content.format(
                working_dir=self.working_directory,
                user_msg=escaped_message
            )
            
            # Write the script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(formatted_script)
                temp_script_path = temp_file.name
            
            try:
                # Run the script
                result = subprocess.run([sys.executable, temp_script_path], 
                                      capture_output=True, text=True, 
                                      cwd=self.working_directory, timeout=30)
                
                if result.returncode == 0:
                    response = result.stdout.strip()
                    if response:
                        return response
                    else:
                        return f"I received your message: '{message}'. I'm your IT Help Desk Agent. How can I help you today?"
                else:
                    error_msg = result.stderr.strip()
                    return f"I received your message: '{message}'. I'm your IT Help Desk Agent. How can I help you today? (Note: {error_msg})"
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_script_path)
                except:
                    pass
            
        except Exception as e:
            return f"Error processing message: {str(e)}"

# Initialize the web agent
web_agent = WebAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/experts') # This is the endpoint for the experts
def experts():
    try:
        experts_file = os.path.join(web_agent.working_directory, 'tech_experts.json')
        with open(experts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return app.response_class(response=json.dumps(data), mimetype='application/json')
    except Exception as e:
        return app.response_class(response=json.dumps({"error": str(e)}), status=500, mimetype='application/json')

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
    
    print("Starting Web-based IT Help Desk Agent with MCP Integration...")
    print("Open your browser and go to: http://localhost:5001")
    socketio.run(app, debug=True, host='127.0.0.1', port=5001)
