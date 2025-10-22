# ChatMRPT Frontend

React-based frontend for ChatMRPT malaria risk analysis platform.

## Tech Stack

- **React** + **TypeScript**
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management

## Structure

- **src/components/** - React components organized by feature
- **src/services/** - API clients and external services
- **src/stores/** - Zustand state stores
- **src/hooks/** - Custom React hooks
- **src/contexts/** - React context providers

## Key Features

- Conversational chat interface with streaming responses
- Interactive visualization rendering
- LLM arena mode for model comparison
- File upload and data management
- Real-time analysis progress tracking

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Builds to `dist/` which is copied to `app/static/react/` for Flask serving.
