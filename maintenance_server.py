from fastmcp import FastMCP
import psutil
import subprocess
import platform
import winreg
import json

# Initialize FastMCP server
mcp = FastMCP("maintenance-server")

@mcp.tool()
def get_heavy_processes(count: int = 5) -> str:
    """
    Returns the top N processes consuming the most CPU and Memory.
    Useful for identifying resource hogs.
    """
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            p.cpu_percent() # First call often returns 0.0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Wait a tiny bit for cpu_percent to be meaningful if needed, 
    # but for simplicity we rely on the iterator or a second pass if strictly needed.
    # psutil.process_iter yields processes. cpu_percent(interval=None) is non-blocking.
    
    # To get accurate CPU, we ideally need an interval, but that blocks.
    # We will just grab current snapshot.
    
    process_list = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            process_list.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    # Sort by CPU usage descending
    sorted_by_cpu = sorted(process_list, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:count]
    
    return json.dumps(sorted_by_cpu, indent=2)

@mcp.tool()
def get_zombie_processes() -> str:
    """
    Finds and returns a list of zombie processes.
    Zombie processes are dead processes that haven't been reaped by their parent.
    """
    zombies = []
    for p in psutil.process_iter(['pid', 'name', 'status']):
        try:
            if p.status() == psutil.STATUS_ZOMBIE:
                zombies.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if not zombies:
        return "No zombie processes found."
    
    return json.dumps(zombies, indent=2)

@mcp.tool()
def get_startup_apps() -> str:
    """
    Lists applications configured to start automatically on boot.
    Supports Windows Registry checks.
    """
    system = platform.system()
    startup_items = []

    if system == "Windows":
        locations = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        ]

        for hkey, path in locations:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({
                                "name": name,
                                "command": value,
                                "location": path
                            })
                            i += 1
                        except OSError:
                            break
            except OSError:
                continue
                
        return json.dumps(startup_items, indent=2)
    
    elif system == "Linux":
        # Basic check for systemd services or .config/autostart
        # This is a simplified check
        return "Linux startup app check not fully implemented in this version."
    
    else:
        return "Unsupported Operating System for startup apps."

@mcp.tool()
def get_update_info() -> str:
    """
    Checks for system update information.
    Windows: Lists recently installed hotfixes.
    Linux: Lists upgradable packages (requires apt).
    """
    system = platform.system()
    
    if system == "Windows":
        # Get installed updates (HotFixes)
        try:
            cmd = ["powershell", "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10 | Format-List"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return f"Recent Installed Updates:\n{result.stdout}"
        except Exception as e:
            return f"Error checking Windows updates: {str(e)}"
            
    elif system == "Linux":
        # Check for upgradable packages
        try:
            cmd = ["apt", "list", "--upgradable"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        except FileNotFoundError:
            return "apt command not found."
        except Exception as e:
            return f"Error checking Linux updates: {str(e)}"
            
    else:
        return "Unsupported Operating System for update info."

if __name__ == "__main__":
    mcp.run()
