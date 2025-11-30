import gradio as gr
import time
import json
from agent_core import create_agent

# Global state
LOGS = []
AGENT = None

def log_callback(msg):
    global LOGS
    LOGS.append(msg)

def get_logs():
    return "\n".join(LOGS)

def init_agent():
    global AGENT
    if AGENT is None:
        AGENT = create_agent(log_callback)
    return AGENT

# --- UI Logic ---

def user_message(user_input, history):
    return "", history + [[user_input, None]]

async def bot_response(history):
    agent = init_agent()
    user_input = history[-1][0]
    
    # Clear logs for new turn if it's a new command
    # global LOGS
    # LOGS = [] 
    
    # Run agent
    # In a real app, we'd use a generator or thread for streaming.
    # Here we simulate streaming by yielding logs as they appear (if we could),
    # but since invoke is blocking, we'll just run it and then update.
    # To make it look "live", we could run it in a thread, but let's keep it simple first.
    
    response = await agent.invoke({"input": user_input})
    output = response["output"]
    
    # Check for approval
    show_approval = False
    if "APPROVAL REQUIRED" in output:
        show_approval = True
        # Parse the action to show?
    
    # Ensure output is a string
    if isinstance(output, dict):
        # If it's a dictionary (like a JSON object), convert it to a string
        output = json.dumps(output, ensure_ascii=False, indent=2)
    elif not isinstance(output, str):
        output = str(output)
        
    history[-1][1] = output
    return history, get_logs(), gr.update(visible=show_approval), gr.update(visible=not show_approval)

def scan_action(history):
    return user_message("Please check my PC security status.", history)

def approve_action(history):
    # User clicked "Approve"
    # We send a hidden message or just trigger the next step
    # For the chat history, we can add "승인합니다"
    history.append(["Approved.", None])
    return "", history

def deny_action(history):
    history.append(["Denied.", "Operation cancelled."])
    return "", history, get_logs(), gr.update(visible=False), gr.update(visible=True)

# --- Layout ---

with gr.Blocks(title="MCP Sentinel", theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate")) as demo:
    gr.Markdown("# 🛡️ MCP Sentinel: Local Security Auditor")
    
    with gr.Row():
        # Left Panel: Interaction
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(height=500, label="Security Session")
            msg = gr.Textbox(label="Command", placeholder="Type 'scan' or 'help'...")
            
            with gr.Row():
                scan_btn = gr.Button("🔍 Start Full Scan", variant="primary")
                report_btn = gr.Button("📄 Generate Report")
            
            # Approval Zone (Hidden by default)
            with gr.Group(visible=False) as approval_group:
                gr.Markdown("### ⚠️ Approval Required")
                gr.Markdown("The agent wants to execute a critical action.")
                with gr.Row():
                    approve_btn = gr.Button("✅ Approve", variant="stop")
                    deny_btn = gr.Button("❌ Deny")

        # Right Panel: Transparency
        with gr.Column(scale=1):
            status_indicator = gr.Markdown("### 🟢 Status: Idle")
            
            gr.Markdown("### 🧠 Thought Stream")
            log_display = gr.TextArea(label="Agent Logs", lines=20, interactive=False)
            
            gr.Markdown("### 📊 Live Visuals")
            # Placeholder for visuals
            visuals = gr.JSON(label="Detected Threats", value={"status": "No active scan"})

    # Event Wiring
    msg.submit(user_message, [msg, chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot, log_display, approval_group, scan_btn]
    )
    
    scan_btn.click(scan_action, [chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot, log_display, approval_group, scan_btn]
    )
    
    approve_btn.click(approve_action, [chatbot], [msg, chatbot]).then(
        bot_response, [chatbot], [chatbot, log_display, approval_group, scan_btn]
    )
    
    deny_btn.click(deny_action, [chatbot], [msg, chatbot, log_display, approval_group, scan_btn])

if __name__ == "__main__":
    demo.launch()
