#!/usr/bin/env python3
"""
Web-based IT Help Desk Agent Launcher
This script starts the web interface for the FastAgent
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Web-based IT Help Desk Agent...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('web_agent.py'):
        print("❌ Error: web_agent.py not found in current directory")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if templates directory exists
    if not os.path.exists('templates'):
        print("❌ Error: templates directory not found")
        print("Please make sure the web interface files are properly set up")
        sys.exit(1)
    
    try:
        print("📦 Dependencies already installed with uv")
        
        print("🌐 Starting web server...")
        print("📍 Open your browser and go to: http://localhost:5001")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the web agent with MCP integration
        subprocess.run([sys.executable, "web_agent_mcp.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting web agent: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Web agent stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
