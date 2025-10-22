# ChatMRPT Tab/Mode Naming Options

**Date:** 2025-10-05
**Current Issue:** Tab names don't clearly reflect what they actually do

---

## Current Tabs & What They Actually Do

### 1. **"General Analysis"** (Upload Modal)
**What it does:**
- Upload CSV + Shapefile (ward-level data with geographic boundaries)
- Flexible risk analysis and mapping
- User has already prepared their data with environmental factors

**Problems with current name:**
- "General Analysis" is vague
- Doesn't indicate you need prepared data
- Doesn't say what kind of analysis

### 2. **"Test Positivity Analysis"** (Upload Modal)
**What it does:**
- TPR workflow: Upload raw facility testing data
- Guided 3-step process (State → Facility Level → Age Group)
- Automatically extracts environmental variables from backend
- Creates TPR maps and prepares data for risk analysis

**Problems with current name:**
- Too technical for some users
- Doesn't indicate it's a guided workflow
- Doesn't show it prepares data FOR risk analysis

### 3. **"Malaria Risk Analysis"** (Main tab badge)
**What it does:**
- Shows current mode/context
- Not actually a tab, just a label

**Problems:**
- Confusing - everything is malaria risk analysis
- Not specific enough

---

## Suggested Naming Options

### Option A: Workflow-Based (What You're Doing)

| Current Name | New Name | Why |
|--------------|----------|-----|
| General Analysis | **Upload Prepared Data** | Clear - you're uploading already-prepared data |
| Test Positivity Analysis | **Guided TPR Workflow** | Shows it's step-by-step guidance |
| Malaria Risk Analysis (badge) | **Risk Analysis** or **Analysis Mode** | Shorter, clearer context |

**Getting Started text:**
- "Upload your prepared data (CSV and shapefile) in the current tab"
- "Switch to **Guided TPR Workflow** for step-by-step test positivity analysis"

### Option B: Data-Source-Based (Where Your Data Comes From)

| Current Name | New Name | Why |
|--------------|----------|-----|
| General Analysis | **Complete Dataset** | You have everything ready |
| Test Positivity Analysis | **Facility Testing Data** | You only have TPR data |
| Malaria Risk Analysis (badge) | **Analysis** | Simple |

**Getting Started text:**
- "Upload your complete dataset (CSV + shapefile)"
- "Or switch to **Facility Testing Data** if you only have TPR data"

### Option C: User-Intent-Based (What You Want To Do)

| Current Name | New Name | Why |
|--------------|----------|-----|
| General Analysis | **I Have My Data Ready** | Clear user intent |
| Test Positivity Analysis | **Calculate TPR First** | Shows what you'll do |
| Malaria Risk Analysis (badge) | **Risk Analysis** | Simple |

**Getting Started text:**
- "**I Have My Data Ready** - Upload CSV + shapefile"
- "**Calculate TPR First** - Upload facility testing data for guided workflow"

### Option D: Simple & Clear (Recommended)

| Current Name | New Name | Why |
|--------------|----------|-----|
| General Analysis | **Upload Data** | Simple, clear |
| Test Positivity Analysis | **TPR Workflow** | Short, descriptive |
| Malaria Risk Analysis (badge) | **Risk Analysis** | Clear context |

**Getting Started text:**
- "Upload your data files (CSV and shapefile) in the **Upload Data** tab"
- "Or use **TPR Workflow** for guided test positivity rate analysis"

### Option E: Process-Based (Most Descriptive)

| Current Name | New Name | Why |
|--------------|----------|-----|
| General Analysis | **Risk Analysis (Direct)** | Shows you go straight to risk analysis |
| Test Positivity Analysis | **TPR → Risk Analysis** | Shows the flow |
| Malaria Risk Analysis (badge) | Keep as is | Already clear |

**Getting Started text:**
- "**Risk Analysis (Direct)** - Upload prepared CSV + shapefile"
- "**TPR → Risk Analysis** - Start with facility testing data"

---

## My Recommendation: **Option D + Clarifications**

### Proposed Structure

**Main Badge:** "Risk Analysis" (shorter, clearer)

**Upload Modal Tabs:**
1. **"Upload Complete Data"**
   - Description: "Ward-level data with environmental variables (CSV/Excel + Shapefile)"

2. **"TPR Workflow"**
   - Description: "Facility testing data only - We'll guide you through TPR calculation and add environmental data"

3. **"Download Processed Data"** (keep as is - already clear)

**Getting Started Text:**
1. "Upload your data in the **Upload Complete Data** tab (CSV + shapefile)"
2. "Or use **TPR Workflow** if you only have facility testing data"
3. "Ask me any questions about malaria or your data"

---

## Alternative Recommendation: **Super Clear Version**

If you want to be VERY explicit about the difference:

**Upload Modal Tabs:**
1. **"I Have Complete Data"**
   - Subtitle: "CSV with environmental variables + Shapefile"

2. **"I Have TPR Data Only"**
   - Subtitle: "Facility testing data - We'll add environmental variables"

3. **"Download Results"** (instead of "Download Processed Data")

**Getting Started:**
1. "**I Have Complete Data** - Upload CSV + shapefile now"
2. "**I Have TPR Data Only** - We'll guide you through preparation"
3. "Ask questions anytime"

---

## Questions to Help Decide

1. **Who are your users?**
   - Malaria program managers → Use technical terms (TPR, Risk Analysis)
   - General health workers → Use simple language (Testing Data, Analysis)
   - Mixed audience → Use Option D (balanced)

2. **What confuses users most?**
   - Not knowing which tab to use → Use "I Have Complete Data" vs "I Have TPR Data Only"
   - Technical jargon → Use simpler terms
   - Process flow → Show the flow (TPR → Risk)

3. **What's the main workflow?**
   - Most users have complete data → Make that tab first/prominent
   - Most users only have TPR → Make TPR workflow more prominent

---

## Quick Decision Matrix

| If users mainly... | Use this naming |
|-------------------|-----------------|
| Have complete data ready | Option D: "Upload Data" + "TPR Workflow" |
| Only have TPR data | Option E: "Direct Analysis" + "TPR → Risk" |
| Are technical users | Keep current or minor tweaks |
| Are confused about what tab to use | Super Clear: "I Have Complete Data" vs "I Have TPR Data Only" |
| Need hand-holding | Option C: Intent-based naming |

---

## Implementation Files

If you choose an option, I'll update:
- `frontend/src/components/Modal/UploadModal.tsx` (tab names)
- `frontend/src/components/Toolbar/Toolbar.tsx` (badge)
- `frontend/src/components/Chat/ChatContainer.tsx` (getting started text)
- `app/web/routes/core_routes.py` (backend content)

---

**Which option feels right for your users?** Or should we create a custom hybrid?
