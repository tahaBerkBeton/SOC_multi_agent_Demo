# SOC Multi-Agent Demo

## Overview

This repository contains a custom agent SDK inspired by OpenAI's Agents SDK, with a streamlined focus on core functionalities. It allows defining agents with their own model, instruction handoffs, API key, and base URL, making it compatible with various LLM backends, including local setups using the OpenAI open API.

This project demonstrates these capabilities through a demo tailored for a Security Operations Center (SOC) workflow, where multiple agents collaborate to investigate email-based threats, document incidents, and escalate when needed.

### Key Features

- **Shared Conversation Space**: Inspired by Swarms (the first open-sourced agentic workflow by OpenAI), agents share a unified conversation space through handoffs, enabling coherent, context-aware actions across all agents. This approach ensures consistency and improves performance over a traditional delegation model because the agents can keep track of the entire workflow.

- **Workspace Management**: Each agent maintains a dedicated structured, fully editable, and dynamic workspace within its system prompt to log data, track modifications, and share critical information with other agents or external systems. This optional feature enhances the agents' internal reasoning and coordination capabilities.

- **Custom MCP**: A simplified Model Context Protocol (MCP) inspired by Anthropic’s design enables tool discoverability and execution through a client-server dynamic.

### Implementation Highlights

The `agentic_workflow.py` script showcases a fully autonomous workflow that handles agent termination, delegation, and step limitations to prevent infinite loops. The orchestrator strategically plans, assigns tasks, and ensures a seamless flow from investigation to reporting. We have decided to showcase these capabilities on an SOC-focused demo, although the SDK can be used for a variety of workflows, including multi-agent chatbots or autonomous swarms.

---

## Demo Video

[https://github.com/user-attachments/assets/11247f15-bb49-40cb-9a57-a94305cc7ab6](https://github.com/user-attachments/assets/11247f15-bb49-40cb-9a57-a94305cc7ab6)

---

## Prerequisites

- Python 3.9 or higher
- An OpenAI API key, or configuration for another LLM service backend (e.g. Groq, or locally via Ollama, VLLM).
  - This demo was tested with OpenAI’s latest `gpt-4.1-2025-04-14` release.

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
   Open `agentic_workflow.py` and set your LLM service parameters directly in code:

   ```python
   model = "gpt-4.1-2025-04-14"  # Adjust with your preferred model
   base_url = "https://api.openai.com/v1"  # Change for other services
   api_key = "your_api_key_here"
   ```

   Simply replace the values to point at Groq, Ollama, VLLM, or any other endpoint you use.

---

## Usage

Run the demo workflow:

```bash
python agentic_workflow.py
```

This will:

1. Initialize the Orchestrator with a predefined security alert.
2. Delegate email analysis to the Mail Agent.
3. Execute tool calls to log tickets, generate reports, and optionally send SMS alerts.
4. Save conversational transcripts in the `conversations/` directory and agent-generated logs, reports, and sms messages to the `assets/` directory.

---

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

---

## Workflow Description

1. **Orchestrator** assesses a security alert and delegates tasks.
2. **Mail Agent** searches for emails, inspects content and attachments, performs required actions and reports findings.
3. **Orchestrator** uses `log_ticket` and `write_report` to document the incident, and can `send_sms_alert` for critical issues.

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests to enhance functionality, add new tools, or improve documentation.

---

## License

This project is released under the MIT License. You are free to use, modify, and distribute this software.
