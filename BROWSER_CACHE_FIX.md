# Browser Cache Fix Instructions

## The Issue
The browser is caching old JavaScript files, preventing the upload fixes from taking effect.

## Quick Fix
1. **Open Developer Tools** (F12)
2. **Right-click the reload button** 
3. **Select "Empty Cache and Hard Reload"**

## Alternative Methods
- Press `Ctrl + Shift + Delete` and clear "Cached images and files"
- In DevTools → Network tab → Check "Disable cache"
- Use an incognito/private window

## What Was Fixed
1. **SessionDataManager**: Changed from instance methods to static methods
2. **Upload endpoint**: Changed from `/upload_files` to `/upload_both_files`
3. **Cache prevention**: Added no-cache headers for development

## Verification
After clearing cache, the upload modal should work without errors.