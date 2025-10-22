# Stable React Build Placeholder

This directory is reserved for the fallback/stable React build.

- Keep it empty in source control to avoid confusing reviewers with compiled assets.
- When you need to deploy or test the stable fallback, run the React build in `frontend/` and copy the output into this folder (same structure as `app/static/react`).
- These files are served by `/stable` routes in Flask if populated.

Leave a `.gitkeep` file so the directory stays committed without build artifacts.
