# Pre-Post Test Survey Implementation Plan

**Date:** October 1, 2025
**Status:** Planning Phase
**Estimated Duration:** 5-7 days

---

## Overview

Implement a standalone pre-post test survey system that measures knowledge improvement before and after training. The system intelligently determines whether to show a pre-test or post-test based on phone number lookup.

---

## Key Requirements (from Supervisor)

### 1. Single Button Intelligence
- ONE button labeled "Pre/Post Test" in header (next to Survey button)
- System determines pre vs post based on phone number lookup
- Logic:
  - **New phone number** → Show PRE-TEST (full version)
  - **Existing phone number** → Show POST-TEST (shortened version)

### 2. Pre-Test Structure
**Section A: Background Information (NO TIMER)**
- Last 4 digits of phone number (identifier)
- Job title
- Computer skills rating
- Frequency of use questions
- All other demographic info from Page 1

**Section B: Concept Assessment (WITH TIMER)**
- Malaria knowledge questions
- TPR analysis questions
- Visualization questions
- Timer starts when entering this section

### 3. Post-Test Structure
**Section A: Identifier Only**
- Last 4 digits of phone number (for matching with pre-test)
- Skip ALL background information

**Section B: Concept Assessment (WITH TIMER)**
- SAME questions as pre-test concept assessment
- Used to measure improvement

### 4. Consent Form
- Simple clickable link to Google Drive PDF
- Statement: "By clicking Start, you consent to participate in this research"
- No complex modal required

### 5. System Separation
- Separate from existing survey system (for research/publication)
- Can be extracted as standalone code if needed
- Uses similar infrastructure but separate database

---

## Technical Architecture

### Database Design
**New Database:** `instance/prepost_test.db`

**Tables:**

1. **prepost_participants**
```sql
CREATE TABLE prepost_participants (
    phone_last4 TEXT PRIMARY KEY,
    pre_test_session_id TEXT,
    post_test_session_id TEXT,
    pre_test_started_at TIMESTAMP,
    pre_test_completed_at TIMESTAMP,
    post_test_started_at TIMESTAMP,
    post_test_completed_at TIMESTAMP,
    background_data TEXT,  -- JSON with job_title, computer_skills, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

2. **prepost_sessions**
```sql
CREATE TABLE prepost_sessions (
    id TEXT PRIMARY KEY,
    phone_last4 TEXT NOT NULL,
    test_type TEXT NOT NULL,  -- 'pre' or 'post'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'active',  -- 'active', 'completed', 'abandoned'
    FOREIGN KEY (phone_last4) REFERENCES prepost_participants(phone_last4)
)
```

3. **prepost_responses**
```sql
CREATE TABLE prepost_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    section TEXT NOT NULL,  -- 'background' or 'concepts'
    response TEXT NOT NULL,
    time_spent_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES prepost_sessions(id)
)
```

### File Structure

```
app/
├── prepost/
│   ├── __init__.py (Blueprint registration)
│   ├── models.py (Database operations)
│   ├── routes.py (API endpoints)
│   └── questions.py (Question configuration)
├── static/
│   └── js/
│       └── prepost_button.js (Button + logic)
└── templates/
    └── prepost/
        └── index.html (Test interface)
```

### API Endpoints

1. **POST /prepost/api/check-phone**
   - Input: `{phone_last4: "1234"}`
   - Output: `{exists: true/false, test_type: "pre"/"post"}`

2. **POST /prepost/api/start**
   - Input: `{phone_last4: "1234", test_type: "pre"/"post"}`
   - Output: `{session_id: "...", questions: [...], background_data: {...}}`

3. **POST /prepost/api/submit-response**
   - Input: `{session_id: "...", question_id: "...", response: "...", time_spent: 45}`
   - Output: `{success: true}`

4. **POST /prepost/api/complete**
   - Input: `{session_id: "..."}`
   - Output: `{success: true, message: "Test completed"}`

5. **GET /prepost/api/export**
   - Output: CSV with pre-test vs post-test comparison

---

## Implementation Steps

### Phase 1: Backend Setup (Days 1-2)

#### Task 1.1: Database Schema
- [x] Create `app/prepost/models.py`
- [x] Define `PrePostDatabase` class
- [x] Implement table creation methods
- [x] Create helper methods for phone lookup
- [x] Add session management methods

#### Task 1.2: Questions Configuration
- [x] Create `app/prepost/questions.py`
- [x] Define background information questions (Section A)
- [x] Define concept assessment questions (Section B)
- [x] Ensure questions match pre-test and post-test requirements

#### Task 1.3: API Routes
- [x] Create `app/prepost/routes.py`
- [x] Implement `/api/check-phone` endpoint
- [x] Implement `/api/start` endpoint
- [x] Implement `/api/submit-response` endpoint
- [x] Implement `/api/complete` endpoint
- [x] Add error handling and validation

#### Task 1.4: Blueprint Registration
- [x] Create `app/prepost/__init__.py`
- [x] Register blueprint in `app/__init__.py`

### Phase 2: Frontend Development (Days 3-4)

#### Task 2.1: Pre/Post Test Button
- [x] Create `app/static/js/prepost_button.js`
- [x] Add button to navigation bar (similar to survey_button.js)
- [x] Style to match existing UI
- [x] Add click handler

#### Task 2.2: Test Interface HTML
- [x] Create `app/templates/prepost/index.html`
- [x] Add consent form section with Google Drive link
- [x] Add phone number entry screen
- [x] Add question display container
- [x] Add timer display (for concept section only)
- [x] Add navigation controls

#### Task 2.3: JavaScript Handler
- [x] Create test flow handler in `prepost.js`
- [x] Implement phone number lookup logic
- [x] Handle pre-test flow (background + concepts)
- [x] Handle post-test flow (concepts only)
- [x] Implement time tracking (concepts section only)
- [x] Add response submission
- [x] Add progress tracking

### Phase 3: Time Tracking & Logic (Day 5)

#### Task 3.1: Timer Implementation
- [x] Start timer when entering concepts section
- [x] Track time per question
- [x] Store time_spent in database
- [x] Display timer to user (optional)

#### Task 3.2: Section Logic
- [x] Pre-test: Show background questions without timer
- [x] Pre-test: Show concept questions with timer
- [x] Post-test: Skip background questions
- [x] Post-test: Show concept questions with timer

### Phase 4: Data Export & Analysis (Day 6)

#### Task 4.1: Export Functionality
- [x] Create export endpoint
- [x] Generate CSV with columns:
  - phone_last4
  - pre_test_score (if applicable)
  - post_test_score (if applicable)
  - pre_test_time
  - post_test_time
  - improvement_delta
  - background_info (job_title, skills, etc.)

#### Task 4.2: Analytics Dashboard (Optional)
- [ ] Create basic stats endpoint
- [ ] Show aggregate improvement metrics

### Phase 5: Testing & Deployment (Day 7)

#### Task 5.1: Testing
- [x] Test pre-test flow end-to-end
- [x] Test post-test flow end-to-end
- [x] Test phone number matching logic
- [x] Verify time tracking works correctly
- [x] Test data export

#### Task 5.2: Deployment
- [x] Deploy to Instance 1 (3.21.167.170)
- [x] Deploy to Instance 2 (18.220.103.20)
- [x] Verify both instances working
- [x] Test through CloudFront CDN

---

## Question Structure

### Background Information Questions (Pre-Test Only)
1. Last 4 digits of phone number (required)
2. Job title / Role (text)
3. Years of experience (number)
4. Computer skills rating (1-5 scale)
5. Frequency of using similar tools (radio: Daily, Weekly, Monthly, Rarely, Never)

### Concept Assessment Questions (Pre-Test AND Post-Test)
**From Appendix 5 / Supervisor's Document:**

#### Section 1: General Knowledge
1. Urban Microstratification definition (multiple choice)
2. Within Ward Heterogeneity (multiple choice)
3. Malaria Risk Score calculation (short answer)
4. Reprioritization concept (multiple choice)
5. High-Risk Areas characteristics (multiple choice)

#### Section 2: TPR Analysis
6. TPR calculation formula (multiple choice)
7. TPR and environmental risk relationship (multiple choice)
8. Mean TPR interpretation (short answer)
9. TPR imputation methods (multiple choice)

#### Section 3: Visualization
10. TPR distribution map interpretation (multiple choice)
11. EVI and water bodies analysis (multiple choice)
12. Vulnerability map usage (multiple choice with vulnerability map link)
13. ITN distribution planning (short answer)

**Total:** ~5 background + 13 concept questions = **18 questions**

---

## UI/UX Flow

### Initial Screen
```
┌─────────────────────────────────────┐
│   Pre/Post Test Survey              │
│                                     │
│   Consent Notice:                   │
│   By proceeding, you consent to     │
│   participate in this research.     │
│   [Read Consent Form] (link)        │
│                                     │
│   Enter last 4 digits of phone:     │
│   [____]                            │
│                                     │
│   [Start Test]                      │
└─────────────────────────────────────┘
```

### Pre-Test Flow
```
Phone Entry → Background Questions → Concept Questions → Complete
              (No Timer)              (With Timer)
```

### Post-Test Flow
```
Phone Entry → Concept Questions → Complete
              (With Timer)
```

---

## Success Metrics

1. **Phone matching accuracy:** 100% (must correctly identify pre vs post)
2. **Time tracking accuracy:** ±1 second
3. **Response rate:** Track abandonment rate
4. **Data completeness:** All responses captured
5. **Export functionality:** Clean CSV with all data

---

## Risk Mitigation

### Risk 1: Phone Number Collisions
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Use last 4 digits as primary key
- Add validation to prevent duplicates
- Consider adding additional identifier if needed (e.g., initials)

### Risk 2: Users Skip Pre-Test
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Clear instructions at deployment time
- System allows post-test only if pre-test completed (optional enforcement)

### Risk 3: Timer Accuracy Issues
**Likelihood:** Low
**Impact:** Low
**Mitigation:**
- Use client-side and server-side timestamps
- Validate time_spent on backend

---

## Deployment Checklist

- [ ] Create `instance/prepost_test.db` on both instances
- [ ] Update `app/__init__.py` to register prepost blueprint
- [ ] Copy `prepost_button.js` to `/static/js/`
- [ ] Update `index.html` to include prepost_button.js
- [ ] Test on local environment
- [ ] Deploy to Instance 1
- [ ] Deploy to Instance 2
- [ ] Verify CloudFront serves new assets
- [ ] Test end-to-end on production
- [ ] Backup database before going live

---

## Timeline Summary

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1: Backend Setup | 2 days | Database, questions, API routes |
| Phase 2: Frontend Development | 2 days | Button, HTML, JavaScript handler |
| Phase 3: Time Tracking & Logic | 1 day | Timer, section logic |
| Phase 4: Data Export | 1 day | Export CSV, analytics |
| Phase 5: Testing & Deployment | 1 day | E2E testing, production deploy |
| **TOTAL** | **7 days** | |

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1: Backend Setup
3. Create database schema
4. Implement API endpoints
5. Build frontend components
6. Test and deploy

---

**Plan Status:** ✅ APPROVED (Pending confirmation)
**Start Date:** TBD
**Expected Completion:** TBD
