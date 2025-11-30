from fastmcp import FastMCP
import psutil
import subprocess
import platform
import json

# Initialize FastMCP server
mcp = FastMCP("security-server")

@mcp.tool()
def get_open_ports() -> str:
    """
    Returns a list of open ports (LISTEN status).
    Useful for detecting unauthorized services.
    """
    connections = psutil.net_connections(kind='inet')
    open_ports = []
    
    for conn in connections:
        if conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                proc_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = "Unknown"
            
            open_ports.append({
                "port": conn.laddr.port,
                "pid": conn.pid,
                "process": proc_name,
                "address": f"{conn.laddr.ip}"
            })
            
    return json.dumps(open_ports, indent=2)

@mcp.tool()
def get_active_connections() -> str:
    """
    Returns a list of active established connections.
    Useful for detecting external intrusions or suspicious outbound traffic.
    """
    connections = psutil.net_connections(kind='inet')
    active_conns = []
    
    for conn in connections:
        if conn.status == 'ESTABLISHED':
            try:
                proc = psutil.Process(conn.pid)
                proc_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = "Unknown"
            
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
            
            active_conns.append({
                "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                "remote": raddr,
                "pid": conn.pid,
                "process": proc_name
            })
            
    return json.dumps(active_conns, indent=2)

@mcp.tool()
def get_firewall_status() -> str:
    """
    Checks the status of the system firewall.
    Supports Windows (netsh) and Linux (ufw).
    """
    system = platform.system()
    
    try:
        if system == "Windows":
            # Check Windows Firewall status
            result = subprocess.check_output(
                "netsh advfirewall show allprofiles", 
                shell=True, 
                text=True
            )
            return result
        elif system == "Linux":
            # Check UFW status (requires sudo usually, might fail if not root)
            result = subprocess.check_output(
                ["ufw", "status"], 
                text=True
            )
            return result
        else:
            return "Unsupported Operating System for firewall check."
    except subprocess.CalledProcessError as e:
        return f"Error checking firewall: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
def get_auth_logs(count: int = 5) -> str:
    """
    Retrieves recent authentication logs (Login failures).
    Windows: Checks Security Event Log (Event ID 4625 - Failed Login).
    Linux: Checks /var/log/auth.log (requires read permissions).
    """
    system = platform.system()
    
    try:
        if system == "Windows":
            # Powershell command to get failed login attempts
            # Note: This might require Admin privileges to read Security logs
            cmd = [
                "powershell", 
                f"Get-EventLog -LogName Security -InstanceId 4625 -Newest {count} | Select-Object TimeGenerated, Message | Format-List"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return f"Error reading logs (might need Admin): {result.stderr}"
            if not result.stdout.strip():
                return "No recent failed login attempts found."
            return result.stdout
            
        elif system == "Linux":
            # Try reading /var/log/auth.log
            try:
                cmd = ["tail", "-n", str(count), "/var/log/auth.log"]
                result = subprocess.check_output(cmd, text=True)
                return result
            except PermissionError:
                return "Permission denied reading /var/log/auth.log. Run as root/sudo."
        else:
            return "Unsupported Operating System for auth logs."
            
    except Exception as e:
        return f"Error retrieving auth logs: {str(e)}"

if __name__ == "__main__":
    mcp.run()
