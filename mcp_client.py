import json
import sys
import subprocess
import os
import time

# Start the MCP server as a subprocess
project_root = "/mnt/ext-hdd1/yoshioka/github/semantic-scholar-mcp"
python_executable = os.path.join(project_root, ".venv", "bin", "python")
server_module = "semantic_scholar_mcp"

env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(project_root, "src") + os.pathsep + env.get("PYTHONPATH", "")

server_process = subprocess.Popen(
    [python_executable, "-m", server_module],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    env=env
)

time.sleep(5) # Increased sleep time

def send_request(request):
    server_process.stdin.write(json.dumps(request) + '\n')
    server_process.stdin.flush()

# Initialize request
initialize_request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "1.0",
        "capabilities": {},
        "clientInfo": {"name": "Gemini CLI", "version": "1.0"}
    },
    "id": 0
}
send_request(initialize_request)

# Read and process responses
json_rpc_responses_received = 0
while json_rpc_responses_received < 2:
    line = server_process.stdout.readline()
    if not line:
        break
    
    try:
        response = json.loads(line.strip())
        if "jsonrpc" in response:
            print(f"Received JSON-RPC response: {json.dumps(response, indent=2)}")
            json_rpc_responses_received += 1

            if response.get("id") == 0 and "result" in response:
                tool_call_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_papers",
                        "arguments": {
                            "query": "large language models",
                            "limit": 1
                        }
                    },
                    "id": 1
                }
                send_request(tool_call_request)
        else:
            print(f"Received non-JSON-RPC output (likely log): {line.strip()}")
    except json.JSONDecodeError:
        print(f"Received non-JSON output (likely log): {line.strip()}")

stdout, stderr = server_process.communicate(timeout=5)
if stdout:
    print(f"Remaining stdout from server:\n{stdout}")
if stderr:
    print(f"Stderr from server:\n{stderr}")

server_process.terminate()
