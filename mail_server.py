import json
import os
import datetime
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

if __name__ == "__main__":
    srv.run()