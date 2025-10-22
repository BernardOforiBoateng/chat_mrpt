# React Build Placeholder

This directory is intentionally empty.

- The actual React source lives in the top-level `frontend/` project.
- When you run `npm run build` inside `frontend/`, copy the contents of `frontend/dist/` into this folder so Flask can serve the compiled assets.
- Keeping the folder empty in git avoids confusing reviewers with generated files. Only deployment builds should populate it.

The `.gitkeep` file ensures the directory stays in the repository without bundling artifacts.
