# agentic_workflow.py
import json
import re
import datetime
import os
from typing import List, Dict, Any, Optional
from agents import Agent, Runner
from colorama import init, Fore, Back, Style

# UI Color and formatting

init(autoreset=True)
SYSTEM_COLOR = Fore.YELLOW
ORCHESTRATOR_COLOR = Fore.GREEN
MAIL_AGENT_COLOR = Fore.CYAN
TOOL_RESULT_COLOR = Fore.MAGENTA
HANDOFF_COLOR = Fore.BLUE
ERROR_COLOR = Fore.RED
HEADER_COLOR = Fore.WHITE + Back.BLUE
DIVIDER = "-" * 60

def print_system(message):
    print(f"\n{SYSTEM_COLOR}System: {message}{Style.RESET_ALL}")

def print_agent(agent_name, message="", end="\n", flush=True):
    color = ORCHESTRATOR_COLOR if agent_name == "Orchestrator" else MAIL_AGENT_COLOR
    print(f"\n{color}{agent_name}: {Style.RESET_ALL}", end="", flush=True)
    if message:
        print(message, end=end, flush=flush)

def print_tool_result(agent_name, result):
    print(f"\n\n{TOOL_RESULT_COLOR}{agent_name} (tool result): {result}{Style.RESET_ALL}")

def print_handoff(from_agent, to_agent):
    print(f"\n\n{HANDOFF_COLOR}[System: Handing off from {from_agent} to {to_agent}]{Style.RESET_ALL}")

def print_error(message):
    print(f"\n\n{ERROR_COLOR}[System: {message}]{Style.RESET_ALL}")

def print_header(message):
    print(f"\n{HEADER_COLOR}{message}{Style.RESET_ALL}")
    print(DIVIDER)

def print_footer(message):
    print(DIVIDER)
    print(f"{HEADER_COLOR}{message}{Style.RESET_ALL}")


# System messages as global variables

SYSTEM_START_MESSAGE = """
Time: 2024-01-05T15:12:00Z 
Severity: High  
Rule: Suspicious Email detected – Excel Macro Alert  
Source: patrick.tremblay@organization‑a.com  
Dest: sofia.nguyen@organization‑a.com  
Subject: "Re: Sophia, Your Expertise Needed for Key Financial Insights!"  
Action: Allowed  
"""  

ORCHESTRATOR_REMINDER = """You have ended your turn without initiating a followup process meant to complete the task. As the orchestrator, you can either:
1. Handoff to another agent using <handoff>AgentName</handoff> to further complete the task.
2. Execute a tool if it aligns with your strategy to solve the task using <tool_call>{...}</tool_call>.
3. Terminate the workflow if the task is solved using </terminate>
Please choose one of these actions to proceed.
Note that if this situation arises after you made a tool, termination or a handoff call, but no termination, tool result or hanfoff was returned, 
this can be related to an incorrect use of the tags or the tool call.
You must repeat your action until you get a system result."""

SUBAGENT_REMINDER = """You have ended your turn without initiating one of your allowed actions. You can either:
1. Execute a tool call using <tool_call>{...}</tool_call>.
2. Handoff to the orchestrator using <handoff>Orchestrator</handoff>
If you feel you have finished your task, you should handoff to the orchestrator. Otherwise, you can continue with tool calls to accomplish your task. 
Note that if this situation arises after you made a tool or a handoff call, but no tool result or hanfoff was returned, this can be related to an incorrect use of the tags or the tool call.
You must repeat your action until you get a system result. """

SUBAGENT_STEP_LIMIT_MESSAGE = """Hey orchestrator, the turn was given back to you on suspicion that your subagent might have been stuck.
You can refine your plan and hand off to them again, or decide that the workflow has failed and terminate."""

MAX_TOTAL_STEPS_MESSAGE = """The workflow has reached the maximum allowed steps and is being automatically terminated. This is to prevent infinite loops."""


# Helper regex utilities
def extract_tool_call(text: str):
    m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def detect_handoff(text: str):
    m = re.search(r"<handoff>(.*?)</handoff>", text)
    return m.group(1) if m else None


def detect_terminate(text: str):
    return "</terminate>" in text



# Instantiate agents with their MCP servers

os.makedirs("conversations", exist_ok=True)
os.makedirs("workspaces", exist_ok=True)

orchestrator = Agent(
    name="Orchestrator",
    instructions=(
        """You are the Security Incident Response Orchestrator responsible for coordinating and managing security alerts and incidents. Your primary job is to analyze security alerts, determine severity, coordinate investigation, authorize response actions, and ensure proper documentation.

When you receive a security alert:
1. ASSESS the alert details and determine the nature and severity of the potential threat
2. PLAN an investigation and response strategy
3. DELEGATE specialized tasks to appropriate agent specialists by first : wrinting a detailed assignement into their workspace with the assign_task tool, then imperatively handoff.
4. REVIEW findings from specialized agents
5. DECIDE on final remediation actions
6. DOCUMENT in intricate details the incident and response actions undertaken by you and the agents.
7. TERMINATE the workflow once the incident is fully resolved

For email-related threats:
- Delegate to the MailAgent for deep analysis of suspicious emails and attachments. Before delegating, always write the detailed assigned task into the agent's workspace, then handoff.
- Review their findings to determine overall organizational risk
- Authorize blocking of malicious senders, if necessary (step to be taken by the MailAgent, insure immediate further handoff )
- Once All actions have been undertaken by the subagent, ensure appropriate alerts are sent to security teams for severe threats

Remember:
- Security incidents require careful documentation. Use the log_ticket and write_report tools.
- For critical security threats, use send_sms_alert to notify security personnel.
- You can assign tasks to other agents using the assign_task tool.
- End the workflow with </terminate> only when the incident is fully investigated, documented, and remediated."""
    ),
    model="gpt-4.1-2025-04-14",
    base_url="https://api.openai.com/v1",
    api_key="YOUR_KEY",
    workspace=True,
    workdata="{}",
    mcp_server="orchestrator_server.py",
)

mail_agent = Agent(
    name="MailAgent",
    instructions=(
        """You are the Email Security Specialist responsible for analyzing and responding to suspicious email threats. Your expertise is in identifying phishing attempts, malware attachments, and other email-based attacks.

When investigating suspicious emails:
1. SEARCH for all emails from the suspicious sender using search_emails_by_sender
2. INSPECT the specific suspicious email using inspect_email to get full details
3. ANALYZE all attachments using inspect_attachment to detect malware
4. DETERMINE whether the email represents a genuine security threat
5. RECOMMEND appropriate actions based on your analysis
6. EXECUTE remediation actions when authorized (such as blocking senders)
7. REPORT your findings back to the Orchestrator

Email security assessment guidelines:
- Suspicious attachment types include: .zip, .xlsm, .xlsx, .xls, .doc, .docm
- Check for social engineering tactics (urgency, authority claims, unusual requests)
- Look for mismatched or suspicious sender domains
- Be alert to emails that request password entry, financial actions, or opening attachments
- Consider the context and whether the email makes sense for the recipient

Remember:
- Always perform a thorough investigation before making recommendations
- Document your findings with detailed evidence
- Report back to the Orchestrator when your analysis is complete by using <handoff>Orchestrator</handoff>"""
    ),
    model="gpt-4.1-2025-04-14",
    base_url="https://api.openai.com/v1",
    api_key="YOUR_KEY",
    workspace=True,
    workdata="{}",
    mcp_server="mail_server.py",
    handoffs=[orchestrator],
)

# Set up handoffs for the orchestrator
orchestrator.handoffs = [mail_agent]

# Autonomous workflow implementation
def run_agentic_workflow(system_message: str, max_total_steps: int = 20, max_subagent_steps: int = 10):
    """
    Run an autonomous workflow starting with the orchestrator agent and a system message.
    
    Args:
        system_message: The initial system message that kicks off the workflow
        max_total_steps: Maximum total steps in the workflow before forced termination
        max_subagent_steps: Maximum consecutive steps a subagent can take before automatic handoff
    """

    print_header("SECURITY INCIDENT INVESTIGATION STARTED")
    
    active = orchestrator
    convo = []
    total_steps = 0
    current_subagent_steps = 0
    
    # initial system message
    system_msg = system_message or SYSTEM_START_MESSAGE
    print_system(system_msg)
    convo.append({"role": "system", "content": system_msg})
    
    while total_steps < max_total_steps:
        total_steps += 1
        
        # If current agent is not the orchestrator, track consecutive steps
        if active.name != "Orchestrator":
            current_subagent_steps += 1
        else:
            # Reset subagent step counter when orchestrator is active
            current_subagent_steps = 0
        
        # Check if subagent has exceeded max steps
        if current_subagent_steps > max_subagent_steps:
            print_system(SUBAGENT_STEP_LIMIT_MESSAGE)
            convo.append({"role": "system", "content": SUBAGENT_STEP_LIMIT_MESSAGE})
            active = orchestrator
            current_subagent_steps = 0
            continue
        
        print_agent(active.name)
        stream = Runner.run_streamed(active, convo)
        assistant_txt = ""
        terminate_detected = False
        handoff_detected = False
        tool_call_detected = False
        
        for token_chunk in stream:
            tok = token_chunk.choices[0].delta.content or ""
            assistant_txt += tok
            print(tok, end="", flush=True)
            
            # Break streaming early conditions
            if "</tool_call>" in assistant_txt:
                tool_call_detected = True
                break
            if active.name == "Orchestrator" and "</terminate>" in assistant_txt:
                terminate_detected = True
                break
            if "</handoff>" in assistant_txt:
                handoff_detected = True
                break
        
        convo.append({"role": "assistant", "content": assistant_txt})
        
        # Check for termination (Orchestrator only)
        if active.name == "Orchestrator" and detect_terminate(assistant_txt):
            print_header("WORKFLOW TERMINATED BY ORCHESTRATOR")
            break
        
        # Check for tool call
        tc = extract_tool_call(assistant_txt)
        if tc:
            try:
                result = active.RunTool(tc["name"], tc.get("arguments", {}))
                print_tool_result(active.name, result)
                convo.append(
                    {
                        "role": "system",
                        "content": f"<tool_result>{result}</tool_result>",
                    }
                )
                continue  # Give agent another turn with result
            except Exception as e:
                err = f"Tool error: {e}"
                print_error(err)
                convo.append({"role": "system", "content": err})
                continue
        
        # Check for handoff
        target = detect_handoff(assistant_txt)
        if target:
            try:
                prev_name = active.name
                active = active.handoff(target)
                print_handoff(prev_name, active.name)
                # Reset subagent steps counter if we're handing off to orchestrator
                if active.name == "Orchestrator":
                    current_subagent_steps = 0
                continue  # New agent responds
            except ValueError as e:
                err = f"Handoff failed: {e}"
                print_error(err)
                convo.append({"role": "system", "content": err})
                continue
        
        # Check for missing actions and send appropriate reminders
        if active.name == "Orchestrator":
            if not (tc or target or terminate_detected):
                print_system(ORCHESTRATOR_REMINDER)
                convo.append({"role": "system", "content": ORCHESTRATOR_REMINDER})
                continue
        else:
            # For non-orchestrator agents
            if not (tc or target):
                print_system(SUBAGENT_REMINDER)
                convo.append({"role": "system", "content": SUBAGENT_REMINDER})
                continue
    
    # Check if workflow ended due to max steps
    if total_steps >= max_total_steps:
        print_system(MAX_TOTAL_STEPS_MESSAGE)
        convo.append({"role": "system", "content": MAX_TOTAL_STEPS_MESSAGE})
    
    # Save the conversation to a timestamped JSON file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join("conversations", f"workflow_{timestamp}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(convo, f, indent=2, ensure_ascii=False)
    
    print_footer("SECURITY INCIDENT INVESTIGATION COMPLETED")
    print(f"\nWorkflow conversation saved to {filename}")

# Main execution
def main():
    system_message = SYSTEM_START_MESSAGE
    run_agentic_workflow(
        system_message=system_message,
        max_total_steps=20,
        max_subagent_steps=10
    )


if __name__ == "__main__":
    main()
