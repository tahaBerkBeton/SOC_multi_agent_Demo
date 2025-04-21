# SOC Multi-Agent Demo

## Overview

This repository demonstrates a multi-agent architecture simulating a Security Operations Center (SOC) workflow using OpenAI’s API and custom inter-process tool servers. It features:

- **Orchestrator Agent**: Coordinates security alerts, delegates tasks, logs tickets, writes reports, and sends alerts.
- **Mail Agent**: Specializes in email threat analysis, including searching, inspecting emails, scanning attachments, and blocking malicious senders.
- **Custom MCP Protocol**: Implements a simple JSON-over-STDIO protocol (`my_mcp`) to expose tools via `SimpleServer` and interact with them through `SimpleClient`.
- **Workspace Management**: Agents maintain stateful file-based workspaces for task assignments.
- **Logging & Reporting**: Tools for logging incident tickets and generating detailed reports.
- **Sample Data**: A collection of sample emails (`assets/mail.json`) for the Mail Agent to analyze.

## Demo Video

<video controls width="600">
  <source src="Demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Prerequisites

- Python 3.9 or higher
- An OpenAI API key

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tahaBerkBeton/SOC_multi_agent_Demo.git
   cd SOC_multi_agent_Demo
   ```

2. **Install dependencies**
   ```bash
   pip install openai colorama
   ```

3. **Configure API Key**
   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

## Usage

Run the demo workflow:
```bash
python agentic_workflow.py
```
This will:
1. Initialize the Orchestrator with a predefined security alert.
2. Delegate email analysis to the Mail Agent.
3. Execute tool calls to log tickets, generate reports, and optionally send SMS alerts.
4. Save conversational transcripts in the `conversations/` directory and agent workspaces in `workspaces/`.

## File Structure

```
.
├── agentic_workflow.py      # Main script coordinating the agents
├── agents.py                # Agent & Runner classes managing LLM interactions
├── orchestrator_server.py   # Orchestrator tools server
├── mail_server.py           # Mail analysis tools server
├── my_mcp/                  # MCP protocol implementation
│   ├── __init__.py
│   ├── server.py            # SimpleServer for tool hosting
│   └── client.py            # SimpleClient for tool invocation
├── assets/
│   └── mail.json            # Sample email dataset
├── Demo.mp4                 # Video demonstration
└── README.md                # Project overview and usage
```

## Workflow Description

1. **Orchestrator** assesses a security alert and delegates tasks.
2. **Mail Agent** searches for emails, inspects content and attachments, and reports findings.
3. **Orchestrator** uses `log_ticket` and `write_report` to document the incident, and can `send_sms_alert` for critical issues.

## Contributing

Contributions are welcome! Please open issues or submit pull requests to enhance functionality, add new tools, or improve documentation.

## License

This project is released under the MIT License. You are free to use, modify, and distribute this software.

