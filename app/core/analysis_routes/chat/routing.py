"""Routing helpers for analysis chat handlers."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

def _chunk_text_for_streaming(text: str, chunk_size: int = 120):
    """Yield small chunks from text to simulate token streaming."""
    if not text:
        return
    for start in range(0, len(text), chunk_size):
        yield text[start:start + chunk_size]

async def route_with_mistral(message: str, session_context: dict) -> str:
    """
    Use Mistral to intelligently route requests.
    
    Returns:
        'needs_tools' - Route to OpenAI with tools for data analysis
        'can_answer' - Let Mistral/Arena handle the response
        'needs_clarification' - Ask user for clarification
    """
    # Quick routing for obvious cases
    message_lower = message.lower().strip()
    common_greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy']
    
    # Fast-track greetings to avoid unnecessary routing
    if message_lower in common_greetings or any(message_lower.startswith(g) for g in common_greetings):
        return "can_answer"
    
    # Fast-track common small talk
    if message_lower in ['thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay', 'sure', 'yes', 'no']:
        return "can_answer"
    
    # CRITICAL: Tool-specific detection BEFORE Mistral routing
    # This ensures tool requests go to tools, not Arena
    if session_context.get('has_uploaded_files', False):
        # Check for analysis tool triggers
        analysis_triggers = [
            'run the malaria risk analysis',
            'run risk analysis',
            'run analysis',
            'perform analysis',
            'analyze the data',
            'analyze my data',
            'start analysis',
            'complete analysis',
            'run the analysis'
        ]
        if any(trigger in message_lower for trigger in analysis_triggers):
            logger.info(f"Tool detection: Analysis trigger found - routing to tools")
            return "needs_tools"
        
        # Check for visualization tool triggers
        visualization_keywords = ['plot', 'map', 'chart', 'visualize', 'graph', 'show me the', 'display']
        if any(keyword in message_lower for keyword in visualization_keywords):
            # Specific visualization checks
            if 'vulnerability' in message_lower and ('map' in message_lower or 'plot' in message_lower):
                logger.info(f"Tool detection: Vulnerability map trigger - routing to tools")
                return "needs_tools"
            elif 'distribution' in message_lower:
                logger.info(f"Tool detection: Distribution visualization trigger - routing to tools")
                return "needs_tools"
            elif any(word in message_lower for word in ['box plot', 'boxplot', 'histogram', 'scatter', 'heatmap', 'bar chart']):
                logger.info(f"Tool detection: Chart type trigger - routing to tools")
                return "needs_tools"
            # General visualization with data
            elif any(keyword in message_lower for keyword in ['plot', 'map', 'chart', 'visualize']):
                logger.info(f"Tool detection: General visualization trigger - routing to tools")
                return "needs_tools"
        
        # Check for ranking/query tool triggers
        ranking_triggers = [
            'top', 'highest', 'lowest', 'rank', 'list wards', 
            'worst', 'best', 'most at risk', 'least at risk',
            'high risk wards', 'low risk wards'
        ]
        if any(trigger in message_lower for trigger in ranking_triggers) and 'ward' in message_lower:
            logger.info(f"Tool detection: Ranking query trigger - routing to tools")
            return "needs_tools"
        
        # Check for data quality and summary triggers
        data_query_triggers = [
            'check data quality',
            'data quality',
            'check quality',
            'summarize the data',
            'summary of data',
            'data summary',
            'describe the data',
            'what variables',
            'available variables'
        ]
        if any(trigger in message_lower for trigger in data_query_triggers):
            logger.info(f"Tool detection: Data query trigger - routing to tools")
            return "needs_tools"
        
        # Check for intervention planning triggers (especially ITN)
        intervention_triggers = [
            'bed net', 'bednet', 'bed-net', 'itn', 'intervention', 'plan distribution',
            'insecticide', 'spray', 'irs', 'treatment',
            'mosquito net', 'llin', 'distribute net', 'distributing net',
            'net distribution', 'nets distribution', 'distribution of net',
            'allocate net', 'allocation of net', 'plan itn', 'itn planning',
            'itn distribution', 'distribute itn', 'plan high trend', 
            'high trend distribution', 'trend distribution'
        ]
        if any(trigger in message_lower for trigger in intervention_triggers):
            logger.info(f"Tool detection: Intervention planning trigger (ITN) - routing to tools")
            return "needs_tools"
        
        # Check for ITN parameter responses (when user provides net count and household size)
        # These patterns indicate user is responding to ITN prompts
        itn_param_patterns = [
            ('have' in message_lower and 'net' in message_lower and any(char.isdigit() for char in message)),
            ('household size' in message_lower and any(char.isdigit() for char in message)),
            ('average household' in message_lower and any(char.isdigit() for char in message)),
            (any(word in message_lower for word in ['million', 'thousand', 'hundred']) and 'net' in message_lower),
            # Common response patterns
            ('i have' in message_lower and any(word in message_lower for word in ['nets', 'bed nets', 'bednets']) and any(char.isdigit() for char in message))
        ]
        if any(pattern for pattern in itn_param_patterns):
            logger.info(f"Tool detection: ITN parameter response detected - routing to tools")
            return "needs_tools"
        
        # Check for specific ward analysis
        if 'why' in message_lower and 'ward' in message_lower and ('rank' in message_lower or 'high' in message_lower or 'risk' in message_lower):
            logger.info(f"Tool detection: Ward analysis explanation trigger - routing to tools")
            return "needs_tools"
    
    try:
        # Import Ollama adapter
        from app.core.ollama_adapter import OllamaAdapter
        ollama = OllamaAdapter()
        
        # Build context information
        files_info = []
        if session_context.get('has_uploaded_files'):
            if session_context.get('csv_loaded'):
                files_info.append("CSV data")
            if session_context.get('shapefile_loaded'):
                files_info.append("Shapefile")
            if session_context.get('analysis_complete'):
                files_info.append("Analysis completed")
        
        files_str = f"Uploaded files: {', '.join(files_info)}" if files_info else "No files uploaded"
        
        # Create routing prompt
        prompt = f"""You are a routing assistant for ChatMRPT, a malaria risk analysis system.

AVAILABLE CAPABILITIES:

1. TOOLS (require uploaded data to function):
   - Analysis Tools: RunCompleteAnalysis, RunPCAAnalysis, RunCompositeAnalysis
     Purpose: Analyze uploaded malaria data, calculate risk scores, identify high-risk areas
   - Visualization Tools: CreateVulnerabilityMap, CreateBoxPlot, CreateHistogram, CreateHeatmap
     Purpose: Generate maps and charts from uploaded data
   - Export Tools: ExportResults, GenerateReport
     Purpose: Export analysis results to PDF/Excel
   - Data Query Tools: CheckDataQuality, GetSummaryStatistics
     Purpose: Query and examine uploaded data

2. KNOWLEDGE RESPONSES (no data needed):
   - Explain malaria concepts (transmission, epidemiology, prevention)
   - Describe analysis methodologies (PCA, composite scoring, risk assessment)
   - ChatMRPT help and guidance
   - General public health information
   - Answer "what is", "how does", "explain" type questions

Context:
- User has uploaded data: {session_context.get('has_uploaded_files', False)}
- {files_str}

User message: "{message}"

ROUTING DECISION PROCESS:

1. Does the user want to PERFORM AN ACTION on their uploaded data?
   Keywords: analyze, plot, visualize, calculate, generate, create, run, export, check, perform
   → If YES and data exists: Reply NEEDS_TOOLS
   
2. Does the user want INFORMATION or EXPLANATION?
   Keywords: what is, how does, explain, tell me about, describe, why
   → Reply CAN_ANSWER (even if data exists - they want knowledge, not action)

3. Is the message explicitly about their uploaded data?
   Phrases: "my data", "the data", "my file", "the csv", "uploaded"
   → If asking for action: Reply NEEDS_TOOLS
   → If asking for explanation: Reply CAN_ANSWER

CRITICAL EXAMPLES:
With data uploaded:
ANALYSIS REQUESTS → NEEDS_TOOLS:
- "Run the malaria risk analysis" → NEEDS_TOOLS (runs run_complete_analysis tool)
- "perform analysis" → NEEDS_TOOLS (analysis action)
- "run analysis" → NEEDS_TOOLS (analysis action)
- "analyze my data" → NEEDS_TOOLS (explicit data operation)
- "start the analysis" → NEEDS_TOOLS (initiate analysis)

VISUALIZATION REQUESTS → NEEDS_TOOLS:
- "plot vulnerability map" → NEEDS_TOOLS (creates vulnerability visualization)
- "plot me the map distribution of evi" → NEEDS_TOOLS (variable distribution map)
- "show me the distribution" → NEEDS_TOOLS (distribution visualization)
- "create a heatmap" → NEEDS_TOOLS (heatmap generation)
- "plot box plot" → NEEDS_TOOLS (box plot visualization)
- "visualize the data" → NEEDS_TOOLS (data visualization)

RANKING/QUERY REQUESTS → NEEDS_TOOLS:
- "show me top 10 highest risk wards" → NEEDS_TOOLS (ranking query)
- "list the worst affected areas" → NEEDS_TOOLS (ranking query)
- "which wards are at highest risk" → NEEDS_TOOLS (risk ranking)
- "why is kafin dabga ward ranked so highly" → NEEDS_TOOLS (ward analysis)

DATA OPERATIONS → NEEDS_TOOLS:
- "Check data quality" → NEEDS_TOOLS (data quality check)
- "summarize the data" → NEEDS_TOOLS (data summary)
- "what variables do we have" → NEEDS_TOOLS (variable listing)
- "describe my dataset" → NEEDS_TOOLS (dataset description)

INTERVENTION PLANNING → NEEDS_TOOLS:
- "plan bed net distribution" → NEEDS_TOOLS (ITN planning tool)
- "where should we distribute mosquito nets" → NEEDS_TOOLS (intervention targeting)
- "plan IRS campaign" → NEEDS_TOOLS (spray planning)

KNOWLEDGE QUESTIONS → CAN_ANSWER:
- "what is analysis" → CAN_ANSWER (asking for explanation)
- "how does PCA work" → CAN_ANSWER (methodology explanation)
- "what is malaria" → CAN_ANSWER (disease information)
- "explain transmission" → CAN_ANSWER (educational content)
- "who are you" → CAN_ANSWER (identity question)

Without data uploaded:
- "analyze" → CAN_ANSWER (no data to analyze, explain concept)
- "plot" → CAN_ANSWER (no data to plot, explain concept)

Reply ONLY: NEEDS_TOOLS, CAN_ANSWER, or NEEDS_CLARIFICATION"""
        
        # Get Mistral's routing decision
        import asyncio
        response = await ollama.generate_async(
            model="mistral:7b",
            prompt=prompt,
            max_tokens=20,
            temperature=0.1  # Low temperature for consistent routing
        )
        
        # Parse and validate response
        decision = response.strip().upper()
        # Routing decision made
        
        if decision == "NEEDS_TOOLS":
            return "needs_tools"
        elif decision == "CAN_ANSWER":
            return "can_answer"
        elif decision == "NEEDS_CLARIFICATION":
            return "needs_clarification"
        else:
            # Fallback if Mistral gives unexpected response
            logger.warning(f"Unexpected Mistral response: {decision}. Using fallback logic.")
            # Check if message explicitly references data
            message_lower = message.lower().strip()
            data_references = ['my data', 'the data', 'uploaded', 'my file', 'the file', 
                             'my csv', 'the csv', 'analyze this', 'plot my', 'visualize the']
            if any(ref in message_lower for ref in data_references):
                return "needs_tools"
            # Default to conversational for general questions
            return "can_answer"
            
    except Exception as e:
        logger.error(f"Error in Mistral routing: {e}. Using neutral fallback.")
        # When Mistral fails, we don't guess - we ask for clarification
        # This prevents incorrect routing when the system is uncertain
        return "needs_clarification"

__all__ = ["_chunk_text_for_streaming", "route_with_mistral"]
