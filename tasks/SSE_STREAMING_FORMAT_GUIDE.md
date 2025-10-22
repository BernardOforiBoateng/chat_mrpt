# SSE Streaming Format Guide

## Why unified_agent_routes.py Formatting Works Perfectly

Based on analysis of `app/web/routes/unified_agent_routes.py` which has perfect Markdown rendering in the React frontend.

---

## ✅ The Perfect SSE Streaming Pattern

### 1. Server-Sent Events (SSE) Protocol

**Response Setup:**
```python
def generate():
    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
    yield "data: " + json.dumps({"type": "delta", "content": message_text}) + "\n\n"
    yield "data: " + json.dumps({"type": "end"}) + "\n\n"

response = Response(generate(), mimetype='text/event-stream')
response.headers['Cache-Control'] = 'no-cache'
response.headers['Connection'] = 'keep-alive'
return response
```

**Critical Headers:**
- `mimetype='text/event-stream'` - Tells browser it's SSE
- `Cache-Control: no-cache` - Prevents caching
- `Connection: keep-alive` - Keeps stream open

---

### 2. Event Structure (JSON Format)

**Event Types:**
```python
{"type": "start"}                              # Signal stream beginning
{"type": "delta", "content": "text"}          # Content chunk
{"type": "visualizations", "data": [...]}     # Visualization data
{"type": "download_links", "data": [...]}     # Download links
{"type": "error", "message": "error text"}    # Error message
{"type": "end"}                               # Signal stream end
```

**Format Pattern:**
```python
"data: " + json.dumps(event_dict) + "\n\n"
```

- **Prefix:** `"data: "` (SSE protocol requirement)
- **Payload:** JSON object
- **Terminator:** `"\n\n"` (double newline - SSE protocol requirement)

---

### 3. Markdown Formatting Rules (THE KEY!)

**❌ WRONG - What Doesn't Work:**
```python
# DON'T DO THIS - Raw newlines in strings
message = "**Bold text:**\n• Bullet 1\n• Bullet 2"

# DON'T DO THIS - Bold text as headings
message = "**Section Title:**\nContent here"

# DON'T DO THIS - Unicode bullets
message = "• Item 1\n• Item 2"
```

**✅ CORRECT - What Works:**
```python
# Use proper Markdown headings
message = "## Section Title\n\nContent here"
message = "### Subsection\n\nMore content"

# Use Markdown lists
message = "- Item 1\n- Item 2\n- Item 3"

# Add blank lines between sections
message = "## First Section\n\n"
message += "Content for first section.\n\n"
message += "### Subsection\n\n"
message += "- Point 1\n- Point 2\n\n"
```

---

### 4. Real Examples from unified_agent_routes.py

#### Example 1: TPR Workflow Start (Lines 129-135)
```python
def gen_tpr_start():
    yield "data: " + json.dumps({"type": "start"}) + "\n\n"
    if result.get('success'):
        yield "data: " + json.dumps({
            "type": "delta",
            "content": result.get('message', '')
        }) + "\n\n"
    else:
        yield "data: " + json.dumps({
            "type": "error",
            "message": result.get('message', 'TPR workflow failed')
        }) + "\n\n"
    yield "data: " + json.dumps({"type": "end"}) + "\n\n"

response = Response(gen_tpr_start(), mimetype='text/event-stream')
response.headers['Cache-Control'] = 'no-cache'
response.headers['Connection'] = 'keep-alive'
return response
```

**Why this works:**
- Clean JSON structure
- Proper SSE format with `data:` prefix
- Double newline terminators
- No raw `\n` inside JSON strings

#### Example 2: State Selection (Lines 199-202)
```python
message_text = "## Step 1: Choose State\n\n"
message_text += "Your data contains multiple states. Please select which state to analyze:\n\n"
for state in states:
    message_text += f"- {state}\n"
message_text += "\nPlease type the name of the state you'd like to analyze."
```

**Breakdown:**
- `"## Step 1: Choose State\n\n"` → Renders as `<h2>` with vertical spacing
- `"- {state}\n"` → Renders as `<li>` inside `<ul>` with proper styling
- `"\n\n"` between sections → Creates paragraph breaks

#### Example 3: Facility Selection (Lines 184-185)
```python
message_text = f"**State:** {single_state} (auto-selected)\n\n"
message_text += formatter.format_facility_selection_only(facility_analysis)
```

**Note:** This uses formatters which return properly structured Markdown

---

### 5. How Frontend Receives & Renders

**Frontend Event Handling:**
```typescript
// From useMessageStreaming.ts pattern
const eventSource = new EventSource(endpoint);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'delta') {
    // data.content contains Markdown string
    // ReactMarkdown renders it with Tailwind prose classes
    setContent(prev => prev + data.content);
  }
};
```

**ReactMarkdown Rendering:**
```tsx
<ReactMarkdown className="prose prose-sm">
  {content}
</ReactMarkdown>
```

**Tailwind CSS Classes Applied:**
```css
.prose h2 { margin-top: 1.5em; font-size: 1.5em; }
.prose h3 { margin-top: 1.25em; font-size: 1.25em; }
.prose ul { margin-top: 1em; margin-bottom: 1em; }
.prose li { margin-top: 0.5em; }
.prose p + p { margin-top: 1em; }
```

**Result:** Proper semantic HTML with vertical spacing!

---

### 6. The RequestInterpreter Streaming Format (Lines 320-355)

This shows how to convert from RequestInterpreter to SSE:

```python
def generate():
    try:
        yield "data: " + json.dumps({"type": "start"}) + "\n\n"

        # Stream from RequestInterpreter
        for chunk in interpreter.process_message_streaming(message, sess_id, session_data):
            # Convert RequestInterpreter format to SSE format
            if chunk.get('content'):
                yield "data: " + json.dumps({
                    "type": "delta",
                    "content": chunk['content']
                }) + "\n\n"

            # Handle visualizations
            if chunk.get('visualizations'):
                yield "data: " + json.dumps({
                    "type": "visualizations",
                    "data": chunk['visualizations']
                }) + "\n\n"

            # Handle download links
            if chunk.get('download_links'):
                yield "data: " + json.dumps({
                    "type": "download_links",
                    "data": chunk['download_links']
                }) + "\n\n"

            # Check for done signal
            if chunk.get('done'):
                yield "data: " + json.dumps({"type": "end"}) + "\n\n"
                break

    except Exception as e:
        logger.error(f"RequestInterpreter streaming error: {e}", exc_info=True)
        yield "data: " + json.dumps({"type": "error", "message": str(e)}) + "\n\n"
        yield "data: " + json.dumps({"type": "end"}) + "\n\n"

response = Response(generate(), mimetype='text/event-stream')
```

**Key Pattern:**
- Each chunk type maps to an SSE event
- Content is extracted from `chunk['content']` → wrapped in `{"type": "delta", "content": ...}`
- Always end with `{"type": "end"}`

---

### 7. Async Streaming Pattern (Lines 229-264)

For async operations with LangGraph agent:

```python
import asyncio
import threading
import queue as q

event_queue: q.Queue[str] = q.Queue(maxsize=100)
sentinel = object()

async def pump_with_context():
    try:
        async for event in agent.analyze_streaming(message, workflow_context={'stage': 'tpr_completed'}):
            payload = "data: " + json.dumps(event) + "\n\n"
            event_queue.put(payload)
    except Exception as e:
        err = {"type": "error", "message": str(e)}
        event_queue.put("data: " + json.dumps(err) + "\n\n")
    finally:
        event_queue.put(sentinel)

def run_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(pump_with_context())
    finally:
        loop.close()

t = threading.Thread(target=run_loop, daemon=True)
t.start()

def generate():
    while True:
        item = event_queue.get()
        if item is sentinel:
            break
        yield item

response = Response(generate(), mimetype='text/event-stream')
```

**Why this pattern:**
- Async LangGraph agent needs separate thread
- Queue bridges async → sync generator
- Sentinel object signals completion
- Clean separation of concerns

---

## 🎯 Key Takeaways

### DO's:
1. ✅ Use proper Markdown syntax (`##` headings, `-` lists)
2. ✅ Add `\n\n` between sections for paragraph breaks
3. ✅ Wrap everything in JSON with SSE format: `"data: " + json.dumps(event) + "\n\n"`
4. ✅ Use `text/event-stream` mimetype
5. ✅ Set `no-cache` and `keep-alive` headers
6. ✅ Always send `{"type": "start"}` and `{"type": "end"}` signals

### DON'T's:
1. ❌ Don't use bold text (`**Bold:**`) as headings
2. ❌ Don't use unicode bullets (`•`) - use Markdown lists (`-`)
3. ❌ Don't put raw `\n` in content without semantic meaning
4. ❌ Don't skip the double newline terminator
5. ❌ Don't forget proper headers
6. ❌ Don't mix SSE format with other response types

---

## 📊 Comparison: Good vs Bad

### ❌ BAD Example (Old TPR Formatter)
```python
message = "**Step 1: Choose Facility Level**\n"
message += "• Primary (1)\n"
message += "• Secondary (2)\n"
message += "• Tertiary (3)\n"

# Results in:
# - No vertical spacing (no semantic structure)
# - Bold text doesn't create h2/h3 elements
# - Unicode bullets don't create ul/li elements
```

### ✅ GOOD Example (Unified Agent Routes)
```python
message = "## Step 1: Choose Facility Level\n\n"
message += "Select from the following options:\n\n"
message += "- Primary (1)\n"
message += "- Secondary (2)\n"
message += "- Tertiary (3)\n\n"
message += "Type the keyword or number to select.\n"

# Results in:
# - <h2> with margin-top (vertical spacing)
# - <ul><li> elements with proper styling
# - <p> elements with paragraph spacing
```

---

## 🔧 Implementation Checklist

When implementing SSE streaming:

- [ ] Set mimetype to `'text/event-stream'`
- [ ] Set `Cache-Control: no-cache` header
- [ ] Set `Connection: keep-alive` header
- [ ] Send `{"type": "start"}` first
- [ ] Use `"data: " + json.dumps(event) + "\n\n"` format
- [ ] Use proper Markdown syntax in content
- [ ] Add `\n\n` between sections
- [ ] Send `{"type": "end"}` last
- [ ] Handle errors with `{"type": "error", "message": "..."}`
- [ ] For async, use queue + threading pattern

---

## 📝 Template for New SSE Endpoints

```python
@blueprint.route('/api/endpoint', methods=['POST'])
def streaming_endpoint():
    try:
        # Get request data
        data = request.get_json() or {}
        message = data.get('message', '')
        session_id = data.get('session_id')

        # Your logic here
        result = process_message(message, session_id)

        # Format response with proper Markdown
        response_text = "## Result\n\n"
        response_text += f"{result.get('message', '')}\n\n"
        response_text += "### Details\n\n"
        for item in result.get('items', []):
            response_text += f"- {item}\n"

        # SSE generator
        def generate():
            yield "data: " + json.dumps({"type": "start"}) + "\n\n"
            yield "data: " + json.dumps({
                "type": "delta",
                "content": response_text
            }) + "\n\n"
            yield "data: " + json.dumps({"type": "end"}) + "\n\n"

        # Create response with proper headers
        response = Response(generate(), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        return response

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        def gen_err():
            yield "data: " + json.dumps({"type": "start"}) + "\n\n"
            yield "data: " + json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n\n"
            yield "data: " + json.dumps({"type": "end"}) + "\n\n"
        response = Response(gen_err(), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        return response
```

---

## 🎓 Lessons Learned

1. **SSE Protocol is Strict:** Must follow exact format with `data:` prefix and `\n\n` terminator
2. **Markdown Needs Semantic Structure:** ReactMarkdown expects proper Markdown, not bold/bullets
3. **Vertical Spacing Comes from Tailwind:** `prose` classes target semantic HTML (`<h2>`, `<ul>`, `<p>`)
4. **Clean JSON is Critical:** No raw newlines in strings; use Markdown syntax instead
5. **Headers Matter:** Missing headers = broken streaming
6. **Async Needs Bridge:** Queue + threading to bridge async → sync generators

---

**Date:** 2025-10-05
**File Analyzed:** `app/web/routes/unified_agent_routes.py`
**Status:** ✅ Perfect formatting reference for all future streaming endpoints
