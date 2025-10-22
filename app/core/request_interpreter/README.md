# Request Interpreter

Modular LLM request interpretation system (refactored from 2,383-line monolith).

## Key Components

- **main.py** - Main interpreter class integrating all mixins
- **session.py** - Session management mixin
- **tooling.py** - Tool execution and routing mixin
- **streaming.py** - Streaming response handling mixin
- **analysis_tools.py** - Analysis-specific tool integration
- **visualization_tools.py** - Visualization tool integration
- **data_tools.py** - Data access and manipulation tools
- **prompting.py** - Prompt construction utilities

## Purpose

Interprets user requests, manages conversation context, routes to appropriate tools, and streams AI responses. Split into focused mixins for maintainability and testing.
