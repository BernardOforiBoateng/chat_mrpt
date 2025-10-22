# ChatMRPT Arena Mode - Implementation Guide

## Overview
ChatMRPT implements an lmarena.ai-style interface where:
- **General questions** → Routed to 5 local models for comparison
- **Tool-calling tasks** → Routed to OpenAI GPT-4o

## The 5 Arena Models (Current Production)
1. **Llama 3.2 3B** - Latest Meta model, excellent general knowledge
2. **Phi-3 Mini** - Microsoft model, strong reasoning and logic
3. **Gemma 2B** - Google model, reliable factual accuracy
4. **Qwen 2.5 3B** - Alibaba model, good multilingual support
5. **Mistral 7B Q4** - Largest model, most accurate responses

## How Arena Mode Works

### 1. Automatic Routing (Backend)
```python
# app/web/routes/analysis_routes.py
use_arena = True  # Default to Arena for everything

# Only skip Arena if tools are needed
if has_uploaded_files and session.get('last_tool_used'):
    requires_tools = True
    use_arena = False  # Use OpenAI GPT-4o instead
```

### 2. Display Format (lmarena.ai style)
- Show **2 models at a time** (dual panel)
- **3 views total** to display all 5 models:
  - View 1: Llama 3.2 vs Phi-3
  - View 2: Gemma vs Qwen 2.5
  - View 3: Mistral vs Llama 3.2 (top performer)

### 3. User Interaction Flow
```
User types: "What's the best way to analyze malaria data?"
                ↓
Backend: No tools needed → Arena mode
                ↓
Frontend receives: {
  type: 'arena_response',
  responses: [5 model responses],
  view_count: 3
}
                ↓
Frontend shows: View 1 of 3
┌─────────────────────┬─────────────────────┐
│   Assistant A       │   Assistant B       │
│   (Llama 3.2)       │   (Phi-3 Mini)      │
│   [Hidden until vote]│   [Hidden until vote]│
├─────────────────────┴─────────────────────┤
│ [👈 Left] [👉 Right] [🤝 Tie] [👎 Both Bad] │
│            View 1 of 3 [Next >]            │
└────────────────────────────────────────────┘
                ↓
User votes → Models revealed → Click "Next >"
                ↓
Shows View 2 of 3 (Gemma vs Qwen 2.5)
                ↓
User votes → Click "Next >"
                ↓
Shows View 3 of 3 (Mistral vs Llama 3.2)
```

## React Implementation Requirements

### Single Page Application
- **NO routing** - Everything in one interface
- **NO separate pages** for Arena, Analysis, etc.
- Just one continuous chat experience

### Component Structure
```
MainInterface.tsx
├── ChatContainer
│   ├── MessageList
│   │   ├── RegularMessage (normal text response)
│   │   └── ArenaMessage (dual-panel with voting)
│   └── InputArea
└── Sidebar (optional - for file uploads, settings)
```

### ArenaMessage Component
```tsx
interface ArenaMessage {
  type: 'arena_response';
  battleId: string;
  currentView: number;  // 0, 1, or 2
  totalViews: 3;
  responseA: string;
  responseB: string;
  modelA?: string;  // Hidden until vote
  modelB?: string;  // Hidden until vote
}
```

### Key Features
1. **Horizontal voting buttons** (not vertical)
2. **View navigation** ("View 1 of 3" with Next button)
3. **Model names hidden** until after voting
4. **Seamless integration** - Arena messages appear inline with regular chat

### CSS Requirements (from arena.css)
```css
.voting-buttons {
  display: flex !important;
  justify-content: center !important;
  gap: 12px !important;
  flex-wrap: nowrap !important;
}

.vote-btn {
  min-width: 140px !important;
  /* Horizontal layout, not stacked */
}
```

## Backend Integration Points

### 1. Send Message
```javascript
// Regular message
POST /send_message_streaming

// Response varies based on backend routing:
// - If Arena: returns arena_response with 5 model outputs
// - If Tools: returns tool execution results from GPT-4o
```

### 2. Vote Submission
```javascript
POST /api/vote_arena
{
  battle_id: "xyz123",
  vote: "a" | "b" | "tie" | "bad",
  view_index: 0 | 1 | 2
}
```

### 3. Get Next View
The frontend manages view cycling locally - no backend call needed.
Just show the next pair of responses from the initial 5 responses.

## Important Notes
1. **Arena is the default** - Most questions go to Arena
2. **Tool detection is automatic** - Backend decides, not user
3. **5 models total** but only 2 shown at once
4. **Blind testing** - Model names hidden until vote
5. **Continuous chat** - Arena responses are just special message types in the chat stream