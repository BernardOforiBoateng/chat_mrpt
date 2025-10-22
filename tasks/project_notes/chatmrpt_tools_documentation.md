# ChatMRPT Tools Documentation

## Tool Categories and Their Purpose

### 1. DATA_ANALYSIS Tools
**Purpose:** Perform comprehensive malaria risk analysis on uploaded data
**Requires Data:** YES
**Tools:**
- `RunCompleteAnalysis` - Full end-to-end analysis pipeline
- `RunCompositeAnalysis` - Composite score based risk analysis
- `RunPCAAnalysis` - Principal Component Analysis for risk assessment
- `GenerateComprehensiveAnalysisSummary` - Summarize analysis results

**When to use:** When user wants to analyze their uploaded data, run risk assessments, calculate scores

### 2. VISUALIZATION Tools
**Purpose:** Create visual representations of data and analysis results
**Requires Data:** YES
**Tools:**
- Charts: `CreateHistogram`, `CreateViolinPlot`, `CreateDensityPlot`, `CreateScatterPlot`, `CreateCorrelationHeatmap`, `CreateBarChart`, `CreatePieChart`, `CreateBoxPlot`
- Maps: `CreateVulnerabilityMap`, `CreatePCAMap`, `CreateUrbanExtentMap`, `CreateInterventionMap`
- Special: `CreateDecisionTree`, `CreateBubbleMap`, `CreateCoordinatePlot`

**When to use:** When user wants to visualize, plot, chart, map, or display their data

### 3. KNOWLEDGE Tools
**Purpose:** Provide general information about malaria, epidemiology, and public health concepts
**Requires Data:** NO
**Tools:**
- `ChatMRPTHelpTool` - Help about using ChatMRPT
- Knowledge base responses about malaria concepts

**When to use:** When user asks "what is", "explain", "how does X work", general questions

### 4. SYSTEM Tools
**Purpose:** Check system status and data availability
**Requires Data:** MAYBE
**Tools:**
- Check data availability
- Get session status
- Get available variables
- Get ward information

**When to use:** When checking what data is loaded, system status queries

### 5. ITN_PLANNING Tools
**Purpose:** Plan Insecticide-Treated Net distribution
**Requires Data:** YES
**Tools:**
- `PlanITNDistribution` - Calculate ITN needs and distribution strategy

**When to use:** When planning interventions, ITN distribution, resource allocation

### 6. SETTLEMENT Tools
**Purpose:** Analyze settlement patterns and building footprints
**Requires Data:** YES (settlement data)
**Tools:**
- `CreateSettlementAnalysisMap` - Map settlement patterns
- `CreateInterventionTargetingMap` - Target interventions by settlement
- Settlement validation and statistics tools

**When to use:** When working with settlement data, building footprints, urban/rural classification

### 7. METHODOLOGY Tools
**Purpose:** Explain analysis methodologies and approaches
**Requires Data:** NO
**Tools:**
- `ExplainAnalysisMethodology` - Explain PCA, composite scoring, etc.

**When to use:** When user asks about methodology, how analysis works, technical details

### 8. EXPORT Tools
**Purpose:** Export results in various formats
**Requires Data:** YES
**Tools:**
- `ExportITNResults` - Export ITN planning results
- Export analysis results to PDF/Excel

**When to use:** When user wants to download, export, or save results

## Key Insights

### Tools That DON'T Need Data (Can Answer Anytime)
1. **Knowledge/Help tools** - General information
2. **Methodology tools** - Explain concepts
3. **Some system tools** - Basic status checks

### Tools That NEED Data
1. **All analysis tools** - Need data to analyze
2. **All visualization tools** - Need data to visualize
3. **ITN planning tools** - Need population/risk data
4. **Settlement tools** - Need settlement/shapefile data
5. **Export tools** - Need results to export

## Current Routing Problem

The system currently uses hardcoded patterns like:
```python
if "analyze" in message:
    route_to_tools()
elif "what is" in message:
    route_to_arena()
```

This fails because:
1. **Context ignored** - "analyze" could mean "analyze the concept" (general) or "analyze my data" (tools)
2. **Tool capabilities ignored** - Not checking if tools can actually handle the request
3. **Brittle patterns** - New phrasings break the system
4. **No semantic understanding** - Missing intent behind words

## What We Need

A routing system that:
1. **Understands tool capabilities** - What each tool can do
2. **Checks data requirements** - Does this tool need data? Is data available?
3. **Semantic understanding** - Intent behind the words, not just keyword matching
4. **Context aware** - Consider conversation history and session state
5. **Graceful fallback** - When unsure, ask for clarification