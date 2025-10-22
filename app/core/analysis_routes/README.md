# Analysis Routes

Flask blueprint for conversational analysis endpoints.

## Structure

- **blueprint.py** - Main Flask blueprint registration
- **chat/** - Chat handlers (sync, streaming, arena, routing)
- **handlers.py** - Legacy route handlers
- **handlers_sync.py** - Synchronous chat handlers

## Purpose

Provides HTTP endpoints for chat interactions, streaming responses, arena battles, and LLM routing. Refactored from monolithic routes into modular chat package.
