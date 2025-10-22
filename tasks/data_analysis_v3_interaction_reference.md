# Data Analysis V3 - Interaction Reference Guide
**THIS IS THE NORTH STAR - DO NOT DEVIATE FROM THIS WHEN BUILDING**

## 🎯 Core Principle: Natural Conversation, Hidden Complexity

### ⚡ Key Requirements
1. **NO CODE VISIBLE TO USERS** - Ever. Period.
2. **Response time < 5 seconds** for all queries
3. **Use existing chat interface** - No new UI elements
4. **Natural language only** - Business insights, not technical details
5. **Interactive visualizations** inline in chat
6. **Work across all AWS workers** - Session compatibility

---

## 📋 Typical User Interaction Flow

### Scenario: Health Official Analyzing Malaria Surveillance Data

#### 1️⃣ **Data Upload**
User uploads `malaria_surveillance_2024.csv` via Data Analysis tab

**System Response:**
```
✅ Data successfully loaded!
• 5,000 records from 247 wards
• 24 months of data (Jan 2023 - Dec 2024)
• Variables include: malaria cases, test positivity rate, population, rainfall

How can I help you analyze this data?
```

**Behind the scenes (HIDDEN):**
- File saved to `instance/uploads/{session_id}/`
- Loaded as pandas DataFrame
- Basic profiling completed
- Columns detected and typed

---

#### 2️⃣ **Simple Query**
```
User: How many unique LGAs are in the data?