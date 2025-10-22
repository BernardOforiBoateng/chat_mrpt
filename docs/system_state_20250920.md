# ChatMRPT System State - September 20, 2025

## Working Features as of 2025-09-20

### 1. Frontend Architecture
- **Active Frontend**: React SPA (Single Page Application)
- **Location**: `/app/static/react/`
- **Entry Point**: `send_from_directory()` serves React `index.html`
- **NOT USED**: Template-based frontend at `/app/templates/index.html`

### 2. Survey Module ✅ WORKING
- **Backend**: `/app/survey/` - Models, routes, questions from Appendix 5
- **Frontend Integration**: `survey_button.js` dynamically injects button into React
- **Script Location**: `/app/static/js/survey_button.js`
- **Must Include**: `<script src="/static/js/survey_button.js" defer></script>` in React index.html
- **Database**: 84 questions loaded in `instance/survey.db`
- **Features**:
  - Auto-detection of arena comparisons
  - Pending survey badges
  - Context-aware questions

### 3. Visualization System ✅ FIXED
- **React Component**: `/frontend/src/components/Visualization/VisualizationContainer.tsx`
- **Explain Feature**: Connected to backend `/explain_visualization` endpoint
- **Backend Service**: `UniversalVizExplainer` using Selenium + GPT-4 Vision
- **Disabled Scripts**: 
  - `visualization_handler.js` - Was causing duplicates
  - `viz_injector.js` - Was causing duplicates
- **No Fallback Messages**: Errors show as "ERROR: [actual message]"

### 4. Infrastructure
- **Production Instances**:
  - Instance 1: 3.21.167.170 (i-0994615951d0b9563)
  - Instance 2: 18.220.103.20 (i-0f3b25b72f18a5037)
- **Access URL**: https://d225ar6c86586s.cloudfront.net
- **ALB**: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
- **Port Config**: Gunicorn on port 8000, ALB expects port 8000
- **Redis**: chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379

### 5. Deployment Requirements
- **CRITICAL**: Always deploy to BOTH production instances
- **React Changes**: Must include survey_button.js script tag
- **Service Restart**: `sudo systemctl restart chatmrpt` on both instances
- **CloudFront**: May need cache invalidation (currently expired credentials)

## Backup Information
- **Backup Created**: ChatMRPT_working_survey_viz_20250920_062245.tar.gz (350MB)
- **Location**: /home/ec2-user/ on Instance 1
- **Contains**: All application code, survey module, React frontend
- **Excludes**: Virtual environments, uploads, compiled Python

## Key Files to Preserve
1. `/app/static/react/index.html` - Must include survey_button.js
2. `/app/static/js/survey_button.js` - Survey injection script
3. `/frontend/src/components/Visualization/VisualizationContainer.tsx` - Fixed viz component
4. `/app/survey/` - Complete survey module
5. `/app/services/universal_viz_explainer.py` - Vision-based explainer

## Known Issues Resolved
- ✅ Duplicate visualization headers - Fixed by disabling conflicting JS
- ✅ Survey button missing - Fixed by restoring script tag
- ✅ Explain button not working - Fixed by removing fallback messages
- ✅ White space on website - Fixed (was port mismatch, now resolved)

## Git Status
- Last commit: d92faac - docs: Update CLAUDE.md with latest AWS backup information
- Survey implementation: Commits a584cd4, 0655d5e, 7519f05, d17e508
- Modified files need commit for survey_button.js restoration
