# Core Module

Central utilities and core functionality for ChatMRPT's conversational AI system.

## Key Components

- **request_interpreter/** - Refactored LLM request interpretation system (modular mixins)
- **analysis_routes/** - Blueprint for analysis chat and streaming endpoints
- **llm_manager.py** - LLM client management (OpenAI, Mistral routing)
- **tool_registry.py** - Central registry for all analysis tools
- **session_state.py** - Session state management
- **arena_manager.py** - LLM arena battle system
- **redis_state_manager.py** - Redis-backed distributed state

## Purpose

Provides the foundational infrastructure for AI-powered conversations, tool execution, session management, and multi-worker coordination across the application.
