import os
import json
import datetime
import re
from my_mcp.server import SimpleServer


# Initialize server
srv = SimpleServer("OrchestratorServer")

# Create assets directory if it doesn't exist
os.makedirs("assets", exist_ok=True)

@srv.tool()
def log_ticket(status: str, outcome: str, ticket_id: str = None) -> dict:
    """
    Log a ticket with a short status description in the logs file.
    
    Args:
        status: A very short description of the operation status
        outcome: The result of the operation, must be 'success' or 'failure'
        ticket_id: Optional ticket identifier (will be auto-generated if not provided)
    
    Returns:
        Ticket details including ID and timestamp
    """
    # Validate outcome
    if outcome.lower() not in ['success', 'failure']:
        return {
            "error": "Outcome must be either 'success' or 'failure'",
            "status": "invalid_input"
        }
    
    # Generate ticket ID if not provided
    if not ticket_id:
        ticket_id = f"TICKET-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create log entry
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = {
        "ticket_id": ticket_id,
        "timestamp": timestamp,
        "status": status,
        "outcome": outcome.lower()
    }
    
    # Append to log file
    log_file_path = os.path.join("assets", "ticket_logs.json")
    
    try:
        # Read existing logs if file exists
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        else:
            logs = []
        
        # Append new log
        logs.append(log_entry)
        
        # Write back to file
        with open(log_file_path, "w") as f:
            json.dump(logs, f, indent=2)
        
        return {
            "ticket_id": ticket_id,
            "timestamp": timestamp,
            "status": "Ticket logged successfully",
            "outcome": log_entry["outcome"]
        }
    except Exception as e:
        return {
            "error": f"Failed to log ticket: {str(e)}",
            "ticket_id": ticket_id
        }

@srv.tool()
def write_report(title: str, content: str, filename: str = None) -> dict:
    """
    Write a detailed report summarizing an operation to a text file.
    
    Args:
        title: The title of the report
        content: The full content/body of the report
        filename: Optional custom filename (will be auto-generated if not provided)
    
    Returns:
        Report details including path and status
    """
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.txt"
    
    # Ensure filename has .txt extension
    if not filename.endswith(".txt"):
        filename += ".txt"
    
    report_path = os.path.join("assets", filename)
    
    try:
        # Format report with title and timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_report = f"""
{title.upper()}
Generated: {timestamp}
{'=' * 50}

{content}

{'=' * 50}
Report End
"""
        
        # Write to file
        with open(report_path, "w") as f:
            f.write(formatted_report)
        
        return {
            "status": "success",
            "filename": filename,
            "path": report_path,
            "message": "Report written successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to write report: {str(e)}"
        }

@srv.tool()
def send_sms_alert(recipient: str, message: str) -> dict:
    """
    Send a short SMS message to notify a security operator (dummy implementation).
    
    Args:
        recipient: Phone number or identifier of the recipient
        message: Short alert message to send (max 160 characters)
    
    Returns:
        Delivery status and details
    """
    # Truncate message if too long for SMS
    if len(message) > 160:
        message = message[:157] + "..."
    
    # Dummy implementation - just log the SMS
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Log the SMS details to a file for simulation purposes
    sms_log_path = os.path.join("assets", "sms_alerts.json")
    
    try:
        # Read existing SMS logs if file exists
        if os.path.exists(sms_log_path):
            with open(sms_log_path, "r") as f:
                try:
                    sms_logs = json.load(f)
                except json.JSONDecodeError:
                    sms_logs = []
        else:
            sms_logs = []
        
        # Append new SMS
        sms_entry = {
            "timestamp": timestamp,
            "recipient": recipient,
            "message": message
        }
        sms_logs.append(sms_entry)
        
        # Write back to file
        with open(sms_log_path, "w") as f:
            json.dump(sms_logs, f, indent=2)
        
        return {
            "status": "delivered",
            "timestamp": timestamp,
            "recipient": recipient,
            "message_length": len(message),
            "message": "SMS alert sent successfully"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Failed to send SMS: {str(e)}"
        }
    

@srv.tool()
def assign_task(agent_name: str, task_description: str) -> dict:
    """
    Write a task into the workspace of another agent.
    
    Args:
        agent_name: Name of the target agent
        task_description: Description of the task to assign
    
    Returns:
        Status of the operation
    """
    # Construct the workspace path based on agent.py implementation
    workspace_dir = "workspaces"
    workspace_path = os.path.join(workspace_dir, f"{agent_name}_workspace.txt")
    
    # Check if workspace exists
    if not os.path.exists(workspace_path):
        return {
            "status": "error",
            "message": f"Workspace for agent '{agent_name}' not found"
        }
    
    try:
        # Read the current workspace content
        with open(workspace_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update the data section
        data_section_pattern = r'<data>\n(.*?)\n  </data>'
        if re.search(data_section_pattern, content, re.DOTALL):
            # Append the new task to existing data
            updated_content = re.sub(
                data_section_pattern,
                f'<data>\n{task_description}\n  </data>',
                content,
                flags=re.DOTALL
            )
        else:
            return {
                "status": "error",
                "message": "Could not find data section in workspace"
            }
        
        # Update the logs section
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        log_entry = {
            "timestamp": timestamp,
            "action": "task_assigned",
            "by": "planner_agent",
            "summary": f"Task assigned to {agent_name}"
        }
        
        # Extract the current logs
        logs_pattern = r'<logs>\n\s+(\{.*\})\n\s+</logs>'
        logs_match = re.search(logs_pattern, updated_content, re.DOTALL)
        
        if logs_match:
            try:
                logs_data = json.loads(logs_match.group(1))
                logs_data["entries"].append(log_entry)
                updated_logs = json.dumps(logs_data, indent=4)
                
                # Update the logs section
                updated_content = re.sub(
                    logs_pattern,
                    f'<logs>\n    {updated_logs}\n  </logs>',
                    updated_content,
                    flags=re.DOTALL
                )
            except json.JSONDecodeError:
                # If logs JSON is invalid, create a new one
                new_logs = {"entries": [log_entry]}
                updated_content = re.sub(
                    logs_pattern,
                    f'<logs>\n    {json.dumps(new_logs, indent=4)}\n  </logs>',
                    updated_content,
                    flags=re.DOTALL
                )
        else:
            return {
                "status": "error",
                "message": "Could not find logs section in workspace"
            }
        
        # Write the updated content back to the file
        with open(workspace_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        return {
            "status": "success",
            "agent": agent_name,
            "timestamp": timestamp,
            "message": f"Task assigned to {agent_name} successfully"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to assign task: {str(e)}"
        }

if __name__ == "__main__":
    srv.run()