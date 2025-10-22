# Stable Version Access Guide

## Current Stable Version
**Date Created**: January 2, 2025  
**Version Tag**: stable-2025-01-02

## Access Points

### Main Application (For New Updates)
- **CloudFront**: https://d225ar6c86586s.cloudfront.net
- **ALB Direct**: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

### Stable Backup Version
- **CloudFront**: https://d225ar6c86586s.cloudfront.net/stable
- **ALB Direct**: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/stable

## What's Included in Stable Version
✅ **All Working Features as of Jan 2, 2025:**
- Privacy Modal (first-run experience)
- Dark Mode with persistence
- Settings without Analysis Modes section
- Arena Mode with fixed voting
- Arena navigation (Previous/Next buttons, clickable dots)
- Upload Modal with three tabs (Standard, Data Analysis, Download)
- Sidebar closed by default

## How It Works
- The stable version is served from `/app/static/react-stable/`
- It's a complete copy of the current working React build
- Accessible at `/stable` URL path
- Completely independent from main version updates

## Updating the Stable Version
When you want to update the stable backup with a new working version:

```bash
# 1. Copy current React build to stable
cd /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT
cp -r app/static/react app/static/react-stable

# 2. Deploy to production
bash deploy_stable_version.sh
```

## Testing Changes
You can now safely make changes to the main application while keeping the stable version accessible:

1. **Test new features**: Deploy to main path (`/`)
2. **Compare versions**: Open both URLs in different tabs
3. **Rollback if needed**: Simply copy stable back to main

## Quick Commands

### View stable version locally
```bash
# Serve from react-stable directory
cd app/static/react-stable
python -m http.server 8001
# Access at http://localhost:8001
```

### Restore stable to main if needed
```bash
cd /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT
cp -r app/static/react-stable/* app/static/react/
npm run build  # In frontend directory
bash deploy_all_fixes.sh
```

## Important Notes
- The stable version will remain unchanged until you explicitly update it
- Users can always access the working version at `/stable`
- This allows safe experimentation with new features
- Both versions share the same backend API