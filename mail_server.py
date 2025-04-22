import json
import os
import datetime
import re
from my_mcp.server import SimpleServer

# Initialize server
srv = SimpleServer("MailServer")

# Load email data
def load_emails():
    """Load emails from the JSON file"""
    file_path = os.path.join('assets', 'mail.json')
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading mail data: {e}")
        return []

# Tool 1: Search emails by sender
@srv.tool()
def search_emails_by_sender(sender: str) -> list:
    """
    Search for emails from a specific sender and return metadata with truncated body.
    
    Args:
        sender: Email address of the sender to search for
    
    Returns:
        List of email metadata objects with truncated body and attachment info
    """
    emails = load_emails()
    results = []
    
    for email in emails:
        if email["sender"].lower() == sender.lower():
            # Create a truncated preview (first 100 chars)
            body_preview = email["body"][:100] + "..." if len(email["body"]) > 100 else email["body"]
            
            # Format attachment info
            has_attachments = len(email["attachments"]) > 0
            attachment_names = email["attachments"] if has_attachments else []
            
            # Create result with relevant metadata
            result = {
                "id": email["id"],
                "date": email["date"],
                "sender": email["sender"],
                "recipient": email["recipient"],
                "subject": email["subject"],
                "body_preview": body_preview,
                "has_attachments": has_attachments,
                "attachment_names": attachment_names
            }
            results.append(result)
    
    return results

# Tool 2: Inspect email in detail
@srv.tool()
def inspect_email(email_id: str) -> dict:
    """
    Inspect a specific email in detail.
    
    Args:
        email_id: The unique ID of the email to inspect
    
    Returns:
        Complete email details including full body
    """
    emails = load_emails()
    
    for email in emails:
        if email["id"] == email_id:
            return email
    
    return {"error": "Email not found"}

# Tool 3: Inspect attachment (dummy implementation)
@srv.tool()
def inspect_attachment(email_id: str, attachment_name: str) -> dict:
    """
    Inspect an email attachment for security issues.
    
    Args:
        email_id: The unique ID of the email containing the attachment
        attachment_name: The name of the attachment to inspect
    
    Returns:
        Analysis report including malware detection results
    """
    emails = load_emails()
    
    # Find the email
    for email in emails:
        if email["id"] == email_id:
            # Check if the attachment exists
            if attachment_name in email["attachments"]:
                # Dummy implementation: always return malicious for ZIP and Excel files
                is_malicious = attachment_name.endswith(('.zip', '.xlsm', '.xlsx', '.xls'))
                
                return {
                    "attachment_name": attachment_name,
                    "is_malicious": is_malicious,
                    "scan_date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "scan_results": "MALICIOUS" if is_malicious else "CLEAN",
                    "details": "Potential macro malware detected" if is_malicious else "No threats detected"
                }
            else:
                return {"error": f"Attachment '{attachment_name}' not found in email"}
    
    return {"error": "Email not found"}

# Tool 4: Block sender (dummy)
@srv.tool()
def block_sender(sender: str) -> dict:
    """
    Block a specific sender from sending future emails.
    
    Args:
        sender: Email address of the sender to block
    
    Returns:
        Status of the blocking operation
    """
    # Current timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "status": "success",
        "sender": sender,
        "blocked_at": current_time,
        "message": f"Sender {sender} has been blocked. All future emails will be rejected."
    }

# Tool 5: Report to orchestrator
@srv.tool()
def report_to_orchestrator(agent_name: str, report_content: str, report_type: str) -> dict:
    """
    Report findings back to the orchestrator by appending to its workspace.
    
    Args:
        agent_name: Name of the agent sending the report
        report_content: Content of the report
        report_type: Type of report (e.g., 'analysis', 'detection', 'action')
    
    Returns:
        Status of the reporting operation
    """
    # Construct the orchestrator workspace path
    workspace_dir = "workspaces"
    workspace_path = os.path.join(workspace_dir, "orchestrator_workspace.txt")
    
    # Check if workspace exists
    if not os.path.exists(workspace_path):
        return {
            "status": "error",
            "message": "Orchestrator workspace not found"
        }
    
    try:
        # Read the current workspace content
        with open(workspace_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Format the report with a header and timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        formatted_report = f"\n--- REPORT FROM {agent_name.upper()} [{report_type}] AT {timestamp} ---\n{report_content}\n"
        
        # Update the data section by appending the new report
        data_section_pattern = r'(<data>\n)(.*?)(\n  </data>)'
        data_match = re.search(data_section_pattern, content, re.DOTALL)
        
        if data_match:
            # Append the new report to existing data
            existing_data = data_match.group(2)
            updated_data = existing_data + formatted_report
            
            updated_content = re.sub(
                data_section_pattern,
                f'\\1{updated_data}\\3',
                content,
                flags=re.DOTALL
            )
        else:
            return {
                "status": "error",
                "message": "Could not find data section in orchestrator workspace"
            }
        
        # Update the logs section
        log_entry = {
            "timestamp": timestamp,
            "action": "report_received",
            "from": agent_name,
            "type": report_type,
            "summary": f"Report received from {agent_name}"
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
                "message": "Could not find logs section in orchestrator workspace"
            }
        
        # Write the updated content back to the file
        with open(workspace_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        return {
            "status": "success",
            "agent": agent_name,
            "report_type": report_type,
            "timestamp": timestamp,
            "message": f"Report from {agent_name} successfully delivered to orchestrator"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to report to orchestrator: {str(e)}"
        }

if __name__ == "__main__":
    srv.run()
