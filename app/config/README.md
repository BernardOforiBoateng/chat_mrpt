# Configuration Module

Environment-specific configuration management for ChatMRPT.

## Key Files

- **base.py** - Base configuration shared across all environments
- **development.py** - Development environment settings
- **production.py** - Production environment settings
- **redis_config.py** - Redis session management configuration
- **arena_config.py** - LLM arena mode settings

## Purpose

Centralizes application configuration using environment-based classes. Manages database URLs, API keys, feature flags, and environment-specific behaviors.
