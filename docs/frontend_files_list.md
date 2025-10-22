# Frontend Files List - Complete Inventory

## CSS FILES (5 total)

### ACTIVE/LOADED (2 files)
1. **app/static/css/modern-minimalist-theme.css**
   - Lines: 2698
   - Status: ✅ LOADED in index.html
   - Problem: Arena styles at END (lines 2472-2698)

2. **app/static/css/vertical-nav-v2.css**
   - Status: ✅ LOADED in index.html
   - Purpose: Navigation menu styles

### NOT LOADED (3 files)
3. **app/static/css/arena.css**
   - Lines: 227
   - Status: ❌ NOT LOADED (missing from index.html)
   - Purpose: Complete Arena UI styles

4. **app/static/css/style.css**
   - Lines: 2238
   - Status: ❌ REDUNDANT (old main styles)
   - Purpose: Original theme (replaced)

5. **app/static/css/vertical-nav.css**
   - Status: ❌ REDUNDANT (old navigation)
   - Purpose: Original nav (replaced by v2)

## HTML TEMPLATES (2 relevant)

6. **app/templates/index.html**
   - Main template
   - Loads: Bootstrap, Font Awesome, modern-minimalist-theme.css, vertical-nav-v2.css
   - Missing: arena.css

7. **app/templates/arena.html**
   - Arena-specific template

## JAVASCRIPT FILES - Chat Modules

### Core (3 files)
8. **app/static/js/modules/chat/core/message-handler.js**
   - Generates Arena UI HTML
   - Creates voting buttons

9. **app/static/js/modules/chat/core/chat-session.js**
   - Session management

10. **app/static/js/modules/chat/core/stream-handler.js**
    - Response streaming

### Arena (2 files)
11. **app/static/js/modules/chat/arena-handler.js**
    - Arena mode logic

12. **app/static/js/modules/chat/arena-manager.js**
    - Arena state management

### Analysis (3 files)
13. **app/static/js/modules/chat/analysis/risk-analyzer.js**
14. **app/static/js/modules/chat/analysis/data-processor.js**
15. **app/static/js/modules/chat/analysis/report-generator.js**

### Visualization (2 files)
16. **app/static/js/modules/chat/visualization/map-visualizer.js**
17. **app/static/js/modules/chat/visualization/chart-renderer.js**

## UI MODULES

18. **app/static/js/modules/ui/vertical-nav-v2.js**
    - Navigation menu logic

19. **app/static/js/modules/ui/sidebar.js**
    - Sidebar functionality

## DEPLOYMENT SCRIPTS

20. **deploy_arena_css_fix.sh**
    - Deploys CSS to AWS instances

21. **audit_frontend_files.sh**
    - Audits frontend structure

22. **investigate_arena_ui.sh**
    - Investigates Arena issues

## AWS FILES CURRENTLY DEPLOYED

### Instance 1 (3.21.167.170)
- /home/ec2-user/ChatMRPT/app/static/css/modern-minimalist-theme.css
- /home/ec2-user/ChatMRPT/app/static/css/vertical-nav-v2.css
- /home/ec2-user/ChatMRPT/app/static/css/arena.css (exists but not loaded)
- /home/ec2-user/ChatMRPT/app/static/css/style.css (redundant)
- /home/ec2-user/ChatMRPT/app/templates/index.html

### Instance 2 (18.220.103.20)
- Same files as Instance 1

## EXTERNAL DEPENDENCIES

23. **Bootstrap 5.3.2** (CDN)
    - Loaded BEFORE our styles
    - Potential conflicts with .btn classes

24. **Font Awesome 6.4.2** (CDN)
    - Icon library

## SUMMARY COUNTS
- CSS Files: 5 (2 active, 3 redundant)
- HTML Templates: 2
- JavaScript Files: 12
- Deployment Scripts: 3
- External Dependencies: 2
- **Total Files: 24**

## FILES THAT NEED CHANGES
1. **index.html** - Add arena.css reference
2. **modern-minimalist-theme.css** - Remove Arena styles from end
3. **style.css** - Delete (redundant)
4. **vertical-nav.css** - Delete (redundant)