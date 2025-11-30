from fastmcp import FastMCP
import psutil
import json

# Initialize FastMCP server
mcp = FastMCP("SystemMonitor")

@mcp.tool()
def get_active_connections() -> str:
    """
    Returns a JSON string list of current LISTENING network connections.
    Each item contains: port, pid, process_name.
    Useful for detecting open ports and potential security risks.
    """
    connections = []
    # Iterate over all internet connections
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                try:
                    process = psutil.Process(conn.pid)
                    proc_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    proc_name = "Unknown"
                
                connections.append({
                    "port": conn.laddr.port,
                    "pid": conn.pid,
                    "process_name": proc_name,
                    "status": conn.status
                })
    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps(connections, indent=2)

@mcp.tool()
def get_system_resources() -> str:
    """
    Returns current CPU and Memory usage as a string.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        return f"CPU: {cpu_percent}%, Memory: {memory.percent}%"
    except Exception as e:
        return f"Error fetching resources: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
