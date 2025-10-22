# Authentication Module

User authentication and authorization system for ChatMRPT.

## Key Components

- **models.py** - User data models and database schemas
- **routes.py** - Authentication endpoints (login, logout, registration)
- **decorators.py** - Authentication decorators for route protection
- **google_auth.py** - Google OAuth integration

## Purpose

Manages user sessions, authentication flows, and access control using Flask-Login. Supports both traditional email/password authentication and OAuth providers.
