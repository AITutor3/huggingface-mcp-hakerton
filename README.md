# MCP Sentinel: Local Security Auditor

## mcp-in-action-track-consumer

MCP Sentinel is an intelligent local security auditing agent powered by the **Model Context Protocol (MCP)**. It leverages a suite of specialized MCP servers to inspect, monitor, and maintain your system's security posture, all accessible through a user-friendly **Gradio** interface.

## 🚀 Features

-   **Interactive Security Agent**: Chat with an AI agent to request scans, ask about system status, or authorize maintenance tasks.
-   **Security Scanning**: `security_server.py` provides tools to audit system security settings and identify potential vulnerabilities.
-   **System Information**: `computer_info_server.py` retrieves detailed hardware and software specifications.
-   **System Monitoring**: `system_monitor_server.py` tracks real-time system performance and status.
-   **Maintenance Tasks**: `maintenance_server.py` allows for controlled execution of system maintenance operations.
-   **Human-in-the-Loop Approval**: Critical actions require explicit user approval via the UI, ensuring safety and control.

## 📂 Project Structure

-   **`app.py`**: The main entry point. Launches the Gradio web interface and orchestrates the agent's interaction with the user.
-   **`agent_core.py`**: Contains the core logic for the AI agent, including tool definitions and the decision-making loop.
-   **`mcp_helper.py`**: Helper functions to facilitate communication and integration with MCP servers.
-   **MCP Servers**:
    -   `security_server.py`: Handles security-related queries and actions.
    -   `computer_info_server.py`: Provides system hardware/software info.
    -   `maintenance_server.py`: Executes maintenance scripts/commands.
    -   `system_monitor_server.py`: Monitors system health.

## 🛠️ Installation & Usage

1.  **Prerequisites**:
    -   Python 3.8+
    -   Recommended: A virtual environment (venv)

2.  **Install Dependencies**:
    ```bash
    pip install gradio
    # Add other dependencies as required by the specific MCP implementation
    ```

3.  **Run the Application**:
    ```bash
    python app.py
    ```

4.  **Access the Interface**:
    Open your browser and navigate to the local URL provided by Gradio (usually `http://127.0.0.1:7860`).

## 🛡️ Security Note

This tool is designed for **local usage** to audit your own system. It has capabilities to read system information and execute commands. Always review the actions proposed by the agent before approving them.

## 🤝 Contributing

Feel free to open issues or submit pull requests to enhance the capabilities of MCP Sentinel!
