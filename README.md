# SOC Multi-Agent Demo

## Overview

This repository demonstrates a multi-agent architecture simulating a Security Operations Center (SOC) workflow 
## Demo Video

[https://github.com/user-attachments/assets/11247f15-bb49-40cb-9a57-a94305cc7ab6](https://github.com/user-attachments/assets/11247f15-bb49-40cb-9a57-a94305cc7ab6)

## Prerequisites

- Python 3.9 or higher
- An OpenAI API key, or configuration for another LLM service backend (e.g. Groq, or locally via Ollama, VLLM).
  - This demo was tested with OpenAI’s latest `gpt-4.1-2025-04-14` release.

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

3. **Configure your LLM Backend**
   Open `agentic_workflow.py`  and set your LLM service parameters directly in code:

   ```python

       model="gpt-4.1-2025-04-14", #Adjust with your prefered model
       base_url="https://api.openai.com/v1",  # Change for other services
       api_key="your_api_key_here"

   ```

   Simply replace the values to point at Groq, Ollama, VLLM, or any other endpoint you use.

## Usage

Run the demo workflow:

```bash
python agentic_workflow.py
```

This will:

1. Initialize the Orchestrator with a predefined security alert.
2. Delegate email analysis to the Mail Agent.
3. Execute tool calls to log tickets, generate reports, and optionally send SMS alerts.
4. Save conversational transcripts in the `conversations/` directory and agent generated logs, reports and sms messages to the `Assets/` directory `.

## File Structure

```
.
├── agentic_workflow.py      # Main script coordinating the agents
├── agents.py                # Agent SDK
├── orchestrator_server.py   # Orchestrator tools server
├── mail_server.py           # Mail Agent tools server
├── my_mcp/                  # MCP protocol implementation
│   ├── __init__.py
│   ├── server.py            # SimpleServer for tool hosting
│   └── client.py            # SimpleClient for tool invocation
├── assets/
│   └── mail.json            # Sample email dataset
└── README.md                # Project overview and usage
```

## Workflow Description

1. **Orchestrator** assesses a security alert and delegates tasks.
2. **Mail Agent** searches for emails, inspects content and attachments, performs required actions and reports findings.
3. **Orchestrator** uses `log_ticket` and `write_report` to document the incident, and can `send_sms_alert` for critical issues.

## Contributing

Contributions are welcome! Please open issues or submit pull requests to enhance functionality, add new tools, or improve documentation.

## License

This project is released under the MIT License. You are free to use, modify, and distribute this software.

