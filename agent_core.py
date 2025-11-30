import os
import operator
from typing import Annotated, List, TypedDict, Union, Dict, Any, Callable

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Import MCP Helper
from mcp_helper import MCPClient

# Load environment variables
load_dotenv()

# --- System Prompt ---
SYSTEM_PROMPT = """# Role Definition
You are 'Local Security Auditor', an intelligent agent dedicated to protecting and optimizing the user's local computer.
You must act as a System Engineer and Security Expert with 20 years of experience.
Do not simply list data in response to user questions; instead, analyze it in the order of **"Symptom -> Cause -> Solution"** to provide insightful reports.

# LANGUAGE DIRECTIVE (CRITICAL)
**YOU MUST ANSWER ONLY IN ENGLISH.**
Even if the user asks in Korean or another language, you must translate your internal thought process and output the final response **entirely in English**.
Do not use any Korean characters in your response.

# Core Directives
1. **Safety First:** Never execute commands that modify the system (e.g., kill process, delete file, block firewall) without user approval. Always **Suggest** and wait for approval.
2. **Contextual Analysis:** Do not just say "CPU is high". Be specific, e.g., "Chrome is using 90% CPU, likely due to too many open tabs or a specific site consuming excessive resources."
3. **Paranoid Security:** Treat unknown ports or connections to overseas IPs as 'Suspicious' by default and warn the user.

# Analysis Guidelines

## 1. Performance
- **CPU:** If usage remains above 80%, identify the Top Process. Distinguish whether it is a system process (e.g., kernel_task) or a third-party app.
- **Memory (Critical):** Do not just look at RAM usage; you MUST check **Swap/Pagefile usage**.
    - *Rule:* RAM 90% + Swap increase = "Severe Memory Shortage (Thrashing)". Warn that the PC may freeze.
- **Disk:** If free space is less than 10GB, warn that "OS updates or caching issues may occur."

## 2. Security & Network
- **Open Ports:** Check listening ports using the `get_open_ports` tool.
    - *Safe:* 80(HTTP), 443(HTTPS), 22(SSH - if user is aware).
    - *Suspicious:* 21(FTP), 23(Telnet), 3389(RDP), or unclear ports above 10000.
- **Connections:** For connections in ESTABLISHED state, if `remote_ip` is not a local network (192.168.x.x, 10.x.x.x, etc.), check the connected process name and judge if it is suspicious.

## 3. Maintenance
- **Zombie Processes:** Processes with `ZOMBIE` status are dead processes taking up memory. Suggest finding the parent process and cleaning them up.

# Response Protocol
All analysis results must follow this format:

## 🛡️ [System Audit Report]
**1. Status Summary:** (e.g., 🟢 Good / 🟡 Attention Needed / 🔴 Danger Detected)
**2. Key Findings:**
   - (Specific fact based on data 1)
   - (Specific fact based on data 2)
**3. Expert Analysis:**
   - (Explanation of causality: why this phenomenon occurred)
**4. Recommended Actions:**
   - [ ] (Actionable suggestions in checkbox format)
   - (Reason why action is needed)

# Interaction Style
- When using technical terms (PID, Port, Swap, etc.), add easy-to-understand explanations in parentheses.
- If there are no issues, clearly reassure the user by saying "System is very clean" so they don't feel anxious.
"""

# --- Tools Setup ---
# Tools will be loaded dynamically from MCP servers

# --- LangGraph Setup ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

class LangGraphAgentExecutor:
    def __init__(self, log_callback, api_key):
        self.log_callback = log_callback
        self.api_key = api_key
        self.app = None
        self.mcp_clients = []
        self.conversation_history = [SystemMessage(content=SYSTEM_PROMPT)]
        
    async def initialize(self):
        self.log_callback("[System] Connecting to MCP Servers...")
        
        # Define servers
        server_files = [
            "computer_info_server.py",
            "security_server.py",
            "maintenance_server.py"
        ]
        
        tools = []
        for server_file in server_files:
            full_path = os.path.abspath(server_file)
            client = MCPClient(full_path)
            try:
                await client.connect()
                self.mcp_clients.append(client)
                server_tools = await client.get_tools()
                tools.extend(server_tools)
                self.log_callback(f"[System] Connected to {server_file} ({len(server_tools)} tools)")
            except Exception as e:
                self.log_callback(f"[Error] Failed to connect to {server_file}: {e}")

        self.tools = tools

        # Initialize Model
        model_name = "gemini-2.5-flash" 
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0
        ).bind_tools(tools)

        # Build Graph
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.execute_tools)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        workflow.add_edge("tools", "agent")
        
        self.app = workflow.compile()
        self.log_callback("[System] Agent initialized with MCP tools.")

    async def call_model(self, state: AgentState):
        messages = state['messages']
        self.log_callback(f"[LangGraph] Invoking model with {len(messages)} messages")
        response = await self.llm.ainvoke(messages)
        return {"messages": [response]}

    async def execute_tools(self, state: AgentState):
        last_message = state['messages'][-1]
        tool_calls = last_message.tool_calls
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_id = tool_call['id']
            
            self.log_callback(f"[MCP] Executing tool: {tool_name} with args: {tool_args}")
            
            # Find the tool in our loaded tools to get the right client/wrapper
            # Since we wrapped them in mcp_helper, we can just execute the wrapper
            # But to be "explicit" about MCP, let's find the client that owns this tool?
            # Actually, the tools list we passed to bind_tools contains the wrappers.
            # We can just use those wrappers.
            
            # However, since we want to show we are using MCP, let's iterate through our tools list
            # and find the matching one.
            
            # Note: In a more complex setup, we might map tool_name -> client.
            # Here, we rely on the fact that the tools list has the wrappers.
            
            # We need to access the 'tools' list which is local to initialize.
            # So we should store it in self.tools
            
            try:
                # Execute the tool
                # We need to find the tool object. 
                # Since we didn't store self.tools, let's fix that in initialize first? 
                # Or we can just rely on the fact that we can re-construct the call or use the bound tools.
                
                # Better approach: We stored the tools in self.tools (we need to add this to initialize)
                # For now, let's assume we have self.tools
                
                selected_tool = next((t for t in self.tools if t.name == tool_name), None)
                
                if selected_tool:
                    # Execute the async wrapper
                    # The wrapper expects **kwargs
                    output = await selected_tool.coroutine(**tool_args)
                else:
                    output = f"Error: Tool {tool_name} not found."
                    
                self.log_callback(f"[MCP] Tool Output: {str(output)[:100]}...")
                
            except Exception as e:
                output = f"Error executing tool {tool_name}: {str(e)}"
                self.log_callback(f"[MCP] Error: {str(e)}")

            results.append(ToolMessage(tool_call_id=tool_id, name=tool_name, content=str(output)))
            
        return {"messages": results}

    def should_continue(self, state: AgentState):
        last_message = state['messages'][-1]
        if last_message.tool_calls:
            self.log_callback(f"[LangGraph] Tool calls detected: {len(last_message.tool_calls)}")
            return "continue"
        return "end"

    async def invoke(self, inputs: Dict[str, Any]):
        if not self.app:
            await self.initialize()
            
        user_input = inputs.get("input", "")
        self.log_callback(f"[LangGraph] Processing: {user_input}")
        
        # Add user message to conversation history
        self.conversation_history.append(HumanMessage(content=user_input))
        
        # Create initial state with full conversation history
        initial_state = {"messages": self.conversation_history.copy()}
        
        try:
            final_state = await self.app.ainvoke(initial_state)
            
            # Get the last message (assistant's response)
            last_message = final_state["messages"][-1]
            
            # Update conversation history with all new messages from this turn
            new_messages = final_state["messages"][len(self.conversation_history):]
            self.conversation_history.extend(new_messages)
            
            # Extract content from the message
            content = last_message.content
            
            # Handle different content formats from Gemini
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, str):
                        text_parts.append(part)
                output_text = '\n'.join(text_parts)
            elif isinstance(content, str):
                output_text = content
            else:
                output_text = str(content)
            
            return {"output": output_text}
        except Exception as e:
            self.log_callback(f"[Error] LangGraph Error: {str(e)}")
            if "404" in str(e) or "not found" in str(e).lower():
                 return {"output": f"Error: Model 'gemini-2.5-flash' not found. Please check your API key or model name.\nDetails: {str(e)}"}
            return {"output": f"An error occurred: {str(e)}"}
            
    async def cleanup(self):
        for client in self.mcp_clients:
            await client.cleanup()

# --- Factory ---

def create_agent(log_callback: Callable[[str], None]):
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        log_callback("[System] Initializing LangGraph Agent with Gemini...")
        return LangGraphAgentExecutor(log_callback, api_key)
    else:
        log_callback("[System] API Key missing. Please set GOOGLE_API_KEY in .env")
        # Return a dummy object that complains
        class ErrorAgent:
            def invoke(self, x): return {"output": "Error: GOOGLE_API_KEY not found in .env file."}
        return ErrorAgent()
