# mcp-server-template-python

A very simple Python template for building MCP servers using Streamable HTTP transport.

## Overview
This template provides a foundation for creating MCP servers that can communicate with AI assistants and other MCP clients. It includes a simple HTTP server implementation with example tools, resource & prompts to help you get started building your own MCP integrations.

## Prerequisites
- Install uv (https://docs.astral.sh/uv/getting-started/installation/)

## Installation

1. Clone the repository:

```bash
git clone git@github.com:alpic-ai/mcp-server-template-python.git
cd mcp-server-template-python
```

2. Install python version & dependencies:

```bash
uv python install
uv sync --locked
```

## Usage

Start the server on port 3000:

```bash
uv run server.py
```

## Running the Inspector

### Requirements
- Node.js: ^22.7.5

### Quick Start (UI mode)
To get up and running right away with the UI, just execute the following:
```bash
npx @modelcontextprotocol/inspector
```

The inspector server will start up and the UI will be accessible at http://localhost:6274.
