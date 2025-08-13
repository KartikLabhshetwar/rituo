"""
Startup scripts for Rituo application
Run the MCP server and FastAPI app together
"""
import os
import subprocess
import sys
import signal
import time
from pathlib import Path

def start_services():
    """Start both MCP server and FastAPI app"""
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path.cwd())
    
    processes = []
    
    try:
        print("🚀 Starting Rituo Services")
        print("=" * 40)
        
        # Start MCP server on port 8001
        print("📡 Starting MCP Server on port 8001...")
        mcp_process = subprocess.Popen([
            "uv", "run", "python", "main.py"
        ], env={**os.environ, "PORT": "8001"})
        processes.append(("MCP Server", mcp_process))
        
        # Wait a moment for MCP server to start
        print("   Waiting for MCP server to initialize...")
        time.sleep(5)
        
        # Check if MCP server started successfully
        if mcp_process.poll() is not None:
            print(f"❌ MCP Server failed to start!")
            print(f"   Exit code: {mcp_process.returncode}")
            print("   Check the logs above for more details")
            raise Exception("MCP Server startup failed")
        else:
            print("✅ MCP Server appears to be running")
        
        # Start FastAPI app on port 8000
        print("🌐 Starting FastAPI App on port 8000...")
        api_process = subprocess.Popen([
            "uv", "run", "uvicorn", "app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], env={**os.environ, "API_PORT": "8000"})
        processes.append(("FastAPI App", api_process))
        
        print("\n✅ All services started successfully!")
        print("\n📋 Service URLs:")
        print("   🔗 FastAPI App:  http://localhost:8000")
        print("   🔗 API Docs:     http://localhost:8000/docs")
        print("   🔗 MCP Server:   http://localhost:8001")
        print("   🔗 Frontend:     http://localhost:3000")
        print("\n💡 Press Ctrl+C to stop all services")
        
        # Wait for processes
        for name, process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
        print("👋 All services stopped")
        
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        for name, process in processes:
            try:
                process.terminate()
            except:
                pass
        sys.exit(1)

def start_dev():
    """Start in development mode"""
    start_services()

if __name__ == "__main__":
    start_services()
