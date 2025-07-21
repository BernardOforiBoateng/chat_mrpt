# ChatMRPT Development Guide

## Standard Workflow

Use this workflow when working on a new task:

1. First,  think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items, that you can check off as you complete them.
3. Before you begin, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.
6. In the plan I also want to make sure we are using the right software engineering practices and scalable coding, modlular as well and ensure that no file you write is more than 600 lines.
7. Put all your thoughts, what you learnt, what worked, what didn't, the decisions made for every task in this tasks/project.md. This will help when we want to review stuff. This is a typical project notes. So it should follow standard practice.
8. ALWAYS update tasks/project.md frequently.

Periodically, make sure to commit when it makes sense to do so.

## Tech Stack
- **Framework**: Flask 3.1.1 (Python web framework) with Flask-Login authentication
- **Python**: 3.10+ with virtual environment at `chatmrpt_venv_new/`
- **Database**: SQLite (development) / PostgreSQL (production)
- **Geospatial**: GeoPandas 1.1.0, Shapely 2.1.1, Rasterio 1.4.3, Fiona 1.10.1, GDAL 3.9.x
- **AI/ML**: OpenAI 1.93.0, PyTorch 2.7.1+CUDA, Transformers 4.53.0, Sentence-Transformers 4.1.0, Scikit-learn 1.7.0
- **Frontend**: Vanilla JS with modular architecture, Tailwind CSS
- **Deployment**: AWS EC2 (3.137.158.17) 
- **Authentication**: Flask-Login with session management

## Project Structure
- `app/` - Main application code (Flask app factory pattern)
  - `analysis/` - Malaria risk analysis pipelines (PCA, composite scoring)
    - `pipeline_stages/` - Modular pipeline components (data prep, scoring, utils)
  - `auth/` - Authentication system (models, routes)
  - `config/` - Environment configurations (development, production, testing)
  - `core/` - Core utilities (LLM manager, request interpreter, session state, tool registry/cache/validator)
  - `data/` - Data processing and settlement loading
    - `population_data/` - PBI distribution data for Nigerian states
  - `interaction/` - User interaction tracking system (core, events, storage)
  - `models/` - Data models and legacy compatibility layer
  - `services/` - Service layer with specialized agents
    - `agents/visualizations/` - Visualization agents (composite, PCA)
    - `reports/` - Report generation (modern generator, templates)
    - Earth Engine clients, data extractors, viz services
  - `tools/` - Modular analysis tools (30+ specialized tools)
  - `web/` - Web interface organization
    - `routes/` - Blueprint routes (analysis, core, debug, reports, upload, viz)
    - `admin.py` - Admin dashboard functionality
  - `static/js/modules/` - Modular JavaScript components
    - `chat/` - Chat interface modules (analysis, core, visualization)
    - `data/` - Data management modules
    - `ui/` - UI components (sidebar, etc.)
    - `utils/` - Utility modules
  - `templates/` - Jinja2 HTML templates (including error pages)
- `instance/` - Runtime data (uploads, reports, databases, logs)
- `kano_settlement_data/` - Geospatial settlement footprint data (436MB)
- `aws_files/` - AWS deployment files (keys, IP addresses)
- `tests/` - Unit and integration tests
- `run.py` - Application entry point
- `gunicorn.conf.py` - Production server configuration


## Commands
**IMPORTANT: Always use the virtual environment for all Python commands**

**Note: Virtual environment has been upgraded to `chatmrpt_venv_new/` with enhanced packages including full geospatial support, latest AI/ML libraries, and CUDA compatibility.**

- Activate virtual environment: `source chatmrpt_venv_new/bin/activate` (Linux/WSL) or `chatmrpt_venv_new/Scripts/activate` (Windows)
- `python run.py` - Start development server (http://127.0.0.1:5000) 
- `pip install -r requirements.txt` - Install dependencies
- `chmod +x build.sh && ./build.sh` - Production deployment build
- `gunicorn 'run:app' --bind=0.0.0.0:$PORT` - Production server
- Virtual environment path: `chatmrpt_venv_new/` - ALWAYS activate before running Python commands



## Environment Variables
- `OPENAI_API_KEY` - Required for AI functionality
- `FLASK_ENV` - development/production 
- `SECRET_KEY` - Flask session security
- `DATABASE_URL` - PostgreSQL connection (production only)

## Code Style & Best Practices
- Use Flask app factory pattern with blueprints
- Follow PEP 8 Python style guidelines
- ES6+ JavaScript with async/await patterns
- Import style: `from module import Class` (not `import module`)
- Use type hints in Python functions
- Modular architecture - each tool is self-contained
- Error handling with try/except and proper logging

### Git Commit Guidelines
- **NEVER include Claude signatures** in commit messages (no "🤖", no "Generated with Claude", no "Co-Authored-By: Claude")
- Write clear, concise commit messages focusing on what changed
- Use conventional commit format when applicable (feat:, fix:, docs:, etc.)
- Keep commit messages professional and human-like

### Scalability & Performance Guidelines
- **Tiered Tool Loading**: Use `app/core/tiered_tool_loader.py` for efficient tool loading
- **Session Isolation**: All user data in `instance/uploads/{session_id}/` for multi-user support
- **Eager Loading**: Preload all essential tools and dependencies at startup for optimal performance
- **Memory Management**: Clear session data after analysis completion
- **Caching Strategy**: Cache expensive operations (geospatial processing, AI responses)
- **Database Optimization**: Use indexes on frequently queried columns
- **File Size Limits**: Enforce upload limits to prevent resource exhaustion

### Anti-Hardcoding Policy
- **NEVER hardcode** geographic locations, state names, or dataset-specific values
- **ALWAYS** use dynamic detection and configuration-based approaches
- **REQUIRED**: Ask for explicit permission before hardcoding ANY values
- **Examples of forbidden hardcoding**:
  ```python
  # ❌ FORBIDDEN - Never hardcode locations
  location = "Kano State"
  
  # ✅ CORRECT - Use dynamic detection
  location = data.get('state_name') or detect_state_from_data(data)
  ```
- **Configuration-driven**: Use `app/config/` for environment-specific settings
- **Data-driven**: Extract values from uploaded data rather than assuming
- **Permission-based**: Always ask before adding hardcoded fallbacks

### Code Quality Standards
- **Defensive Programming**: Validate all inputs and handle edge cases
- **Logging Strategy**: Use structured logging with appropriate levels
- **Error Messages**: Provide clear, actionable error messages to users
- **Code Reviews**: All hardcoded values must be justified and approved
- **Documentation**: Document all configuration options and dynamic behaviors
- **Testing**: Write tests that work with multiple datasets, not just one region

## Core Architecture Patterns
- **Service Container**: `app/services/container.py` manages dependency injection
- **Tool System**: Each analysis tool in `app/tools/` follows standard interface
- **Request Interpreter**: `app/core/request_interpreter.py` handles LLM conversation routing
- **Session Management**: Per-user data isolation in `instance/uploads/{session_id}/`
- **Data Pipeline**: Multi-stage analysis in `app/analysis/pipeline.py`

## File Upload Handling
- CSV/Excel: Max 32MB, stored in `instance/uploads/{session_id}/`
- Shapefiles: Uploaded as ZIP, extracted to `shapefile/` subdirectory  
- Settlement data: Large geospatial files in `kano_settlement_data/`
- Generated files: Maps (.html), analysis results (.csv), reports

## Database Schema
- `instance/interactions.db` - User conversations and analysis history
- `instance/agent_memory.db` - AI learning and patterns
- Session-specific CSVs for analysis results and rankings

## Critical Dependencies
- **GDAL/GEOS**: Geospatial processing (available via Rasterio 1.4.3 and Fiona 1.10.1)
- **OpenAI**: Required for conversational AI features (v1.93.0)
- **GeoPandas**: Shapefile and geospatial data processing (v1.1.0)
- **PyTorch**: AI/ML processing with CUDA support (v2.7.1)
- **LangChain**: Conversational AI framework (v0.3.26)
- **ChromaDB**: Vector database for embeddings (v1.0.13)

## Do Not Touch
- Never edit files in `instance/uploads/` manually
- Do not modify `kano_settlement_data/` structure (436MB dataset)
- Do not commit `.env` files or API keys
- Never change database schema without migration planning
- Preserve existing analysis pipeline stages order
- Do not alter settlement type mappings without testing

## Development Workflow Guidelines
- **Code Reviews**: All changes must be reviewed for hardcoding violations
- **Testing Protocol**: Test with multiple datasets from different regions
- **Documentation Updates**: Update CLAUDE.md when adding new patterns or standards
- **Performance Monitoring**: Profile code for scalability bottlenecks
- **Security Checks**: Validate all user inputs and file uploads
- **Deployment Checklist**: Ensure configurations work across environments

## Testing
- Run integration tests: `python -m pytest tests/`
- Health check endpoint: `/ping` and `/system-health`
- Test data uploads using `app/sample_data/` templates

## Deployment
- **Target**: AWS infrastructure /
- **Production Database**: PostgreSQL with persistent storage
- **Build Process**: `build.sh` creates directories and installs system deps
- **Web Server**: gunicorn with Flask application
- **Static Files**: Served through Flask with caching headers
- **Logs**: Rotating file handler in `instance/app.log`
- **Infrastructure**: Scalable for institutional deployment with large geospatial datasets

## Malaria Domain Context
- **Primary Use**: Epidemiological risk assessment for malaria intervention targeting
- **Data Types**: Ward-level demographic, environmental, and health indicators
- **Analysis Methods**: Composite scoring, PCA, vulnerability ranking
- **Output**: Interactive maps, risk rankings, intervention recommendations
- **Geographic Focus**: Nigerian states (Kano reference implementation)

## Session Data Flow
1. User uploads CSV (demographic) + shapefile (boundaries)
2. Data validation and cleaning in `app/data/processing.py`
3. Analysis pipeline: normalize → score → rank → visualize
4. Results stored as session-specific files in `instance/uploads/{session_id}/`
5. Interactive maps generated and served via `/serve_viz_file/` route

## Common File Patterns
- Analysis results: `analysis_*.csv` 
- Visualizations: `*_map_*.html`, `*_chart_*.html`
- Raw uploads: `raw_data.csv`, `raw_shapefile.shp`
- Settlement maps: `building_classification_map_*.html`