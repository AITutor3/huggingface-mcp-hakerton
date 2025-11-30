from fastmcp import FastMCP
import psutil
import json

# Initialize FastMCP server
mcp = FastMCP("computer-info")

@mcp.tool()
def get_cpu_info() -> str:
    """
    Get CPU information including usage, core count, and per-core usage.
    """
    # CPU 전체 사용률 (1초 동안 측정)
    cpu_usage = psutil.cpu_percent(interval=1)

    # 코어(논리 프로세서) 개수
    cpu_count = psutil.cpu_count()

    # 코어별 사용률
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

    result = (
        f"CPU Usage: {cpu_usage}%\n"
        f"Total Cores: {cpu_count}\n"
        f"Usage per Core: {cpu_per_core}"
    )
    return result

@mcp.tool()
def get_memory_info() -> str:
    """
    Get Memory (RAM) information including total, used, and percent.
    """
    # 메모리 상태 가져오기
    memory = psutil.virtual_memory()

    # 바이트(Byte) 단위이므로 보기 좋게 GB로 변환하려면 / (1024**3) 필요
    total = round(memory.total / (1024**3), 2)
    used = round(memory.used / (1024**3), 2)
    percent = memory.percent

    result = (
        f"Total Memory: {total} GB\n"
        f"Used Memory: {used} GB\n"
        f"Memory Usage: {percent}%"
    )
    return result

@mcp.tool()
def get_disk_info() -> str:
    """
    Get Disk information for the root path.
    """
    # 루트 경로(/ 또는 C:\)의 디스크 용량 확인
    # Windows assumes C:\, Linux/Mac assumes /
    import platform
    path = 'C:\\' if platform.system() == 'Windows' else '/'
    
    disk = psutil.disk_usage(path)

    total_disk = round(disk.total / (1024**3), 2)
    used_disk = round(disk.used / (1024**3), 2)
    free_disk = round(disk.free / (1024**3), 2)

    result = (
        f"Total Disk: {total_disk} GB\n"
        f"Used Disk: {used_disk} GB\n"
        f"Free Space: {free_disk} GB"
    )
    return result

@mcp.tool()
def get_network_info() -> str:
    """
    Get Network information including traffic and active connections.
    """
    # 1. 네트워크 트래픽 양 (보낸 양/받은 양)
    net_io = psutil.net_io_counters()
    traffic_info = (
        f"Bytes Sent: {net_io.bytes_sent / (1024**2):.2f} MB\n"
        f"Bytes Received: {net_io.bytes_recv / (1024**2):.2f} MB"
    )

    # 2. 현재 열려있는 포트와 연결 상태 (보안 점검용)
    # *주의: 모든 정보를 보려면 관리자 권한(sudo/admin)으로 실행해야 할 수 있습니다.
    connections = psutil.net_connections(kind='inet')

    conn_info = "\n[Active Network Connections - Top 5]"
    for conn in connections[:5]: # Limit to 5
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
        conn_info += f"\nStatus: {conn.status} | Local: {laddr} | Remote: {raddr} | PID: {conn.pid}"
    
    return traffic_info + conn_info

@mcp.tool()
def get_os_info() -> str:
    """
    Get Operating System information including version, release, and architecture.
    """
    import platform
    import sys
    
    os_name = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    architecture = platform.machine()
    
    result = (
        f"OS: {os_name}\n"
        f"Release: {os_release}\n"
        f"Version: {os_version}\n"
        f"Architecture: {architecture}"
    )
    return result

if __name__ == "__main__":
    mcp.run()
