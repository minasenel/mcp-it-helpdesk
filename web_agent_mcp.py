import asyncio
import json
import os
import sys
import subprocess
import tempfile
import time
import requests
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
        self.django_api_base = 'http://localhost:8000/api'
    
    def create_issue_in_django(self, employee_id, description, category, subcategory, priority):
        """Create an issue in Django database"""
        try:
            payload = {
                'employee_id': employee_id,
                'description': description,
                'category': category,
                'subcategory': subcategory,
                'priority': priority
            }
            response = requests.post(f'{self.django_api_base}/issues/', json=payload, timeout=10)
            if response.status_code == 201:
                data = response.json()
                return data.get('issue_id', f"ISS{data.get('id', '000')}")
            else:
                print(f"Django API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error calling Django API: {e}")
            return None
    
    def assign_expert_in_django(self, issue_id, expert_id):
        """Assign an expert to an issue in Django database"""
        try:
            # First, get the issue to find its Django ID
            issues_response = requests.get(f'{self.django_api_base}/issues/', timeout=10)
            if issues_response.status_code == 200:
                issues = issues_response.json()
                django_issue = None
                for issue in issues:
                    if issue.get('issue_id') == issue_id:
                        django_issue = issue
                        break
                
                if django_issue:
                    print(f"Found Django issue {django_issue['id']} for issue_id {issue_id}")
                    # Call the assign_expert endpoint
                    assign_response = requests.post(
                        f'{self.django_api_base}/issues/{django_issue["id"]}/assign_expert/', 
                        timeout=10
                    )
                    print(f"Assign expert response: {assign_response.status_code} - {assign_response.text}")
                    if assign_response.status_code == 200:
                        return assign_response.json()
                    else:
                        print(f"Expert assignment error: {assign_response.status_code} - {assign_response.text}")
                        return None
                else:
                    print(f"Issue {issue_id} not found in Django database")
                    return None
            else:
                print(f"Error fetching issues: {issues_response.status_code}")
                return None
        except Exception as e:
            print(f"Error assigning expert in Django: {e}")
            return None
    
    def process_message(self, message):
        """Process a message using the MCP tools"""
        try:
            # Import MCP tools directly instead of using subprocess
            sys.path.insert(0, self.working_directory)
            from main import ai_classify_issue, ai_try_solve, add_issue, assign_expert
            import requests
            
            # Process the message directly
            user_message = message
            message_lower = user_message.lower().strip()
            
            # Use AI to classify the issue
            category, subcategory = ai_classify_issue(user_message)
            
            # Check if AI classified it as a non-technical issue
            if category == "software" and subcategory == "general" and len(message_lower.split()) <= 3:
                greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you', 'bye', 'goodbye', 'selam', 'merhaba']
                questions = ['how are you', 'what can you do', 'help me', 'what is this', 'who are you', 'nasılsın', 'ne yapabilirsin']
                
                is_simple_greeting = any(greeting in message_lower for greeting in greetings)
                is_simple_question = any(question in message_lower for question in questions)
                
                if is_simple_greeting or is_simple_question:
                    return """👋 Hello! I'm your IT Help Desk Agent. 

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
            
            # Check if it's a follow-up request for expert assistance
            if any(phrase in message_lower for phrase in [
                'need further assistance', 'assign me with', 'human expert', 'assign expert', 'escalate', 'transfer to',
                'assign me', 'assign an expert', 'assign me an expert', 'assign to human', 'connect me to human',
                'talk to human', 'contact an expert', 'assing expert', 'assing human', 'assing me'
            ]):
                # Load experts and find the best match
                try:
                    experts_file = os.path.join(self.working_directory, "tech_experts.json")
                    with open(experts_file, 'r', encoding='utf-8') as f:
                        experts = json.load(f)
                    
                    available_experts = [expert for expert in experts if expert.get('availability', True)]
                    
                    if available_experts:
                        assigned_expert = available_experts[0]
                        expert_name = assigned_expert.get('name', 'Unknown Expert')
                        expert_contact = assigned_expert.get('contact', 'contact@example.com')
                        expert_skills = ', '.join(assigned_expert.get('expertise', []))
                        expert_id = assigned_expert.get('id', '')
                        
                        # Try to assign expert in Django for the most recent issue
                        try:
                            # Get the most recent issue from Django
                            issues_response = requests.get(f'{self.django_api_base}/issues/', timeout=10)
                            if issues_response.status_code == 200:
                                issues = issues_response.json()
                                if issues:
                                    # Find the most recent issue for WEB_USER that doesn't have an expert assigned
                                    web_user_issues = [issue for issue in issues if issue.get('employee_id') == 'WEB_USER' and not issue.get('assigned_expert_id')]
                                    if web_user_issues:
                                        latest_issue = max(web_user_issues, key=lambda x: x.get('created_at', ''))
                                        print(f"Assigning expert to latest issue: {latest_issue.get('issue_id')} (Django ID: {latest_issue.get('id')})")
                                        # Assign expert to this issue
                                        django_result = self.assign_expert_in_django(latest_issue.get('issue_id'), expert_id)
                                        if django_result:
                                            print(f"✅ Expert assigned in Django: {django_result}")
                                        else:
                                            print("⚠️ Failed to assign expert in Django")
                                    else:
                                        print("No unassigned issues found for WEB_USER")
                        except Exception as e:
                            print(f"Error assigning expert in Django: {e}")
                        
                        return f"""🔄 **Expert Assignment Complete**

**Assigned Expert:** {expert_name}

**Contact Information:** {expert_contact}

**Expertise Areas:** {expert_skills}

**Next Steps:**
• Contact the expert directly using the email above
• Mention your issue details and reference any issue ID you received
• The expert will respond within 24 hours

**Your Issue:** {user_message}

Is there anything else I can help you with?"""
                    else:
                        return f"""🔄 **Expert Assignment Request**

Unfortunately, no experts are currently available. 

**Alternative Options:**
• Try the AI solution provided earlier
• Submit a detailed ticket through our support portal
• Check back in a few hours for expert availability

**Your Issue:** {user_message}

Is there anything else I can help you with?"""
                        
                except Exception as e:
                    return f"""🔄 **Expert Assignment Request**

I understand you need further assistance with your technical issue.

**Your Issue:** {user_message}

**Next Steps:**
• I'll assign you to a human expert who specializes in your issue type
• The expert will contact you within 24 hours
• You'll receive an email with expert contact details

**Current Status:** Your issue has been logged and is being processed.

Is there anything else I can help you with while you wait for the expert?"""
            
            # Check if it's a general question about capabilities
            questions = ['how are you', 'what can you do', 'help me', 'what is this', 'who are you', 'nasılsın', 'ne yapabilirsin']
            if any(question in message_lower for question in questions):
                return """🤖 I'm an IT Help Desk Agent with access to:

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
            
            # If AI couldn't classify it properly, ask for more details
            if category == "software" and subcategory == "general" and len(message_lower.split()) <= 5:
                return f"""❓ I need more details to help you effectively.

Your message: "{user_message}"

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
            
            # Determine priority
            if any(word in message_lower for word in ['urgent', 'critical', 'emergency', 'down', 'broken']):
                priority = "high"
            elif any(word in message_lower for word in ['important', 'soon', 'asap']):
                priority = "medium"
            else:
                priority = "low"
            
            # Try AI solution first
            ai_solution = ai_try_solve(user_message, category, subcategory, priority)
            
            # Create issues in both systems in parallel
            def create_issues():
                # Create in MCP system
                mcp_issue_id = add_issue("WEB_USER", user_message, category, subcategory, priority)
                
                # Create in Django
                django_issue_id = self.create_issue_in_django("WEB_USER", user_message, category, subcategory, priority)
                
                return mcp_issue_id, django_issue_id
            
            # Run issue creation
            mcp_issue_id, django_issue_id = create_issues()
            
            if "Çözüm önerisi bulunamadı" not in ai_solution:
                # AI found a solution
                response = f"""✅ **AI Solution Found!**

**Issue:** {user_message}
**Category:** {category}/{subcategory}
**Priority:** {priority}

**Solution:**
{ai_solution}

**Issue ID:** {mcp_issue_id}"""
                
                if django_issue_id:
                    response += f"\n**Django Issue ID:** {django_issue_id}"
                
                response += "\n\nIs this solution helpful? If you need further assistance, I can assign you to a human expert."
                
            else:
                # AI couldn't solve, assign expert
                try:
                    experts_file = os.path.join(self.working_directory, "tech_experts.json")
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
                        expert_id = assigned_expert.get('id', '')
                        
                        # Assign expert in Django if we have a Django issue ID
                        if django_issue_id:
                            try:
                                print(f"Assigning expert {expert_id} to Django issue {django_issue_id}")
                                django_result = self.assign_expert_in_django(django_issue_id, expert_id)
                                if django_result:
                                    print(f"✅ Expert assigned in Django: {django_result}")
                                else:
                                    print("⚠️ Failed to assign expert in Django")
                            except Exception as e:
                                print(f"Error assigning expert in Django: {e}")
                        else:
                            print("No Django issue ID available for expert assignment")
                        
                        response = f"""🤖 **AI Analysis Complete - Expert Assigned**

**Issue:** {user_message}
**Category:** {category}/{subcategory}
**Priority:** {priority}

**AI Analysis:** I couldn't find an automated solution for this issue.

**Assigned Expert:** {expert_name}
**Contact:** {expert_contact}
**Expertise:** {expert_skills}

**Issue ID:** {mcp_issue_id}"""
                        
                        if django_issue_id:
                            response += f"\n**Django Issue ID:** {django_issue_id}"
                        
                        response += """

**Next Steps:**
• Contact the expert directly using the email above
• Mention your issue details and reference the issue ID
• The expert will respond within 24 hours

A human expert will help you resolve this issue."""
                    else:
                        # Fallback to generic expert assignment
                        expert_assignment = assign_expert(user_message)
                        response = f"""🤖 **AI Analysis Complete**

**Issue:** {user_message}
**Category:** {category}/{subcategory}
**Priority:** {priority}

**AI Analysis:** I couldn't find an automated solution for this issue.

**Expert Assignment:** {expert_assignment}

**Issue ID:** {mcp_issue_id}"""
                        
                        if django_issue_id:
                            response += f"\n**Django Issue ID:** {django_issue_id}"
                        
                        response += "\n\nA human expert will be in touch with you soon to resolve this issue."
                        
                except Exception as e:
                    # Fallback to generic expert assignment
                    expert_assignment = assign_expert(user_message)
                    response = f"""🤖 **AI Analysis Complete**

**Issue:** {user_message}
**Category:** {category}/{subcategory}
**Priority:** {priority}

**AI Analysis:** I couldn't find an automated solution for this issue.

**Expert Assignment:** {expert_assignment}

**Issue ID:** {mcp_issue_id}"""
                    
                    if django_issue_id:
                        response += f"\n**Django Issue ID:** {django_issue_id}"
                    
                    response += "\n\nA human expert will be in touch with you soon to resolve this issue."
            
            return response
            
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
