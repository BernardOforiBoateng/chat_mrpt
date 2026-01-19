# Archived Components - September 20, 2025

## Template-Based Frontend (NOT USED)
- **Original Location**: `/app/templates/`
- **Archived To**: `/app/templates_archived_20250920/`
- **Archive Backup**: `/archived_template_frontend/template_frontend_20250920.tar.gz`
- **Reason**: React frontend is the active frontend; template frontend was causing confusion
- **Note**: Survey templates kept in `/app/templates/survey/` as they are still needed

## Conflicting JavaScript Files
- **Archived Files**:
  - `visualization_handler.js` - Was causing duplicate visualization headers
  - `viz_injector.js` - Was causing duplicate Explain buttons
- **Archived To**: `/app/static/js/archived_unused/`
- **Reason**: These were creating duplicate UI elements conflicting with React components

## What Remains Active
- **React Frontend**: `/app/static/react/` and `/frontend/src/`
- **Survey Button**: `/app/static/js/survey_button.js` - Injects survey into React
- **Survey Backend**: `/app/survey/` - All backend functionality
- **Survey Templates**: `/app/templates/survey/` - Still needed for survey pages

## Important Notes
- The index route serves React: `send_from_directory(..., "react", "index.html")`
- Do NOT use `render_template("index.html")` as that template is archived
- All UI modifications should be made to React components in `/frontend/src/`
