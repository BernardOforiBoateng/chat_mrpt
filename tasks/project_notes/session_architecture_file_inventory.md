# ChatMRPT Session Architecture - Complete File Inventory

## Date: 2025-09-23
## Purpose: Complete inventory of files for session architecture refactoring

## 1. CRITICAL - Singleton/Global State Files (MUST ELIMINATE)

### Core Singletons (These store state in memory - PRIMARY PROBLEM)
- `app/core/unified_data_state.py` - **CRITICAL**: Global `_data_state_manager` stores ALL sessions
- `app/core/analysis_state_handler.py` - Global `_analysis_state_handler`
- `app/core/instance_sync.py` - Global `_instance_sync`
- `app/core/tool_cache.py` - Global `_tool_cache`
- `app/core/redis_state_manager.py` - Global `_redis_state_manager`
- `app/core/arena_context_manager.py` - Global `_arena_context_manager`
- `app/core/tiered_tool_loader.py` - Global `_tiered_loader`
- `app/core/tool_registry.py` - Global `_registry`
- `app/core/llm_manager.py` - Global LLM manager instance
- `app/core/ollama_manager.py` - Global Ollama manager

### Analysis Coordinators (Store analysis state)
- `app/analysis/variable_selection_coordinator.py` - Stores coordinators by session_id
- `app/analysis/variable_comparison_validator.py` - Validator with session state
- `app/data_analysis_v3/core/metadata_cache.py` - Caches metadata in memory
- `app/data_analysis_v3/core/lazy_loader.py` - Lazy loading with caching

## 2. Session Management Files

### Session State Definition
- `app/core/session_state.py` - SessionState dataclass (not singleton but used by singletons)
- `app/services/session_memory.py` - SessionMemory class for conversation history
- `app/core/workflow_state_manager.py` - Workflow state management

### Session Routes
- `app/web/routes/session_routes.py` - Session verification endpoints
- `app/web/routes/core_routes.py` - **CRITICAL**: Creates session_id with `uuid.uuid4()`

## 3. Main Route Files (Entry Points for Requests)

### User-Facing Routes
- `app/web/routes/analysis_routes.py` - Main analysis endpoint (`/send_message`, `/run_analysis`)
- `app/web/routes/upload_routes.py` - File upload handling (`/upload_both_files`)
- `app/web/routes/data_analysis_v3_routes.py` - V3 analysis routes
- `app/web/routes/visualization_routes.py` - Visualization generation
- `app/web/routes/arena_routes.py` - Arena mode routes
- `app/web/routes/itn_routes.py` - ITN distribution routes
- `app/web/routes/export_routes.py` - Data export routes

### Authentication Routes
- `app/auth/routes.py` - Login/logout (sets session data)
- `app/auth/models.py` - User model

## 4. Request Processing Chain

### Request Interpreters (Handle LLM routing)
- `app/core/request_interpreter.py` - **MAJOR**: Main request routing, stores conversation history
- `app/core/simple_request_interpreter.py` - Simplified interpreter
- `app/core/interpreter_migration.py` - Migration utilities

### Arena System (Multi-model system)
- `app/core/arena_manager.py` - Arena battle management
- `app/core/enhanced_arena_manager.py` - Enhanced arena features
- `app/core/arena_data_context.py` - Arena data context
- `app/core/arena_integration_patch.py` - Integration patches
- `app/core/arena_prompt_builder.py` - Prompt building
- `app/core/arena_trigger_detector.py` - Trigger detection

## 5. Data Access Layer

### Data State Management
- `app/data/flexible_data_access.py` - Flexible data access patterns
- `app/data/unified_dataset_builder.py` - Builds unified datasets
- `app/data/loaders.py` - Data loading utilities
- `app/data/processing.py` - Data processing functions
- `app/data/__init__.py` - Data module initialization

### Tool Data Access
- `app/services/tools/get_unified_dataset.py` - Gets unified dataset for tools
- `app/tools/base.py` - Base tool class
- `app/core/direct_tools.py` - Direct tool execution

## 6. Analysis Pipeline Files

### Main Pipeline
- `app/analysis/pipeline.py` - Main analysis pipeline
- `app/analysis/engine.py` - Analysis engine
- `app/analysis/__init__.py` - Analysis initialization
- `app/analysis/itn_pipeline.py` - ITN distribution pipeline
- `app/analysis/pca_pipeline.py` - PCA analysis pipeline

### Pipeline Stages
- `app/analysis/pipeline_stages/data_preparation.py` - Data prep stage
- `app/analysis/pipeline_stages/scoring_stages.py` - Scoring stage
- `app/analysis/pipeline_stages/pipeline_utils.py` - Pipeline utilities

## 7. Service Layer

### Service Container
- `app/services/container.py` - **CRITICAL**: Service dependency injection
- `app/services/__init__.py` - Service initialization

### Visualization Services
- `app/services/visualization/chart_service.py` - Chart generation service
- `app/services/agents/visualizations/composite_visualizations.py` - Composite viz
- `app/services/agents/visualizations/pca_visualizations.py` - PCA viz
- `app/services/agents/visualizations/core_utils.py` - Core utilities

## 8. Configuration Files

### App Configuration
- `app/__init__.py` - **CRITICAL**: Flask app factory, Redis initialization
- `app/config/__init__.py` - Config initialization
- `app/config/base.py` - Base configuration
- `app/config/development.py` - Development config
- `app/config/production.py` - Production config
- `app/config/redis_config.py` - Redis configuration

### Infrastructure Config
- `gunicorn.conf.py` - **CRITICAL**: Worker configuration (`workers=6`, `preload_app=True`)

## 9. Database/Storage Layer

### Interaction Logging
- `app/interaction/__init__.py` - Interaction logging system
- `app/interaction/core.py` - Core interaction functions
- `app/interaction/storage.py` - Storage functions
- `app/interaction/events.py` - Event logging

### Models
- `app/models/data_handler.py` - DataHandler class
- `app/models/analysis.py` - Analysis models

## 10. Utility Files

### Decorators and Validators
- `app/core/decorators.py` - `@validate_session`, `@handle_errors` decorators
- `app/core/tool_validator.py` - Tool validation
- `app/utils/security.py` - Security utilities

### Response Handling
- `app/core/responses.py` - Response formatting
- `app/services/response_formatter.py` - Response formatting service

## 11. Tool System Files

### Tool Loading and Registry
- `app/core/tool_registry.py` - Tool registration system
- `app/core/tiered_tool_loader.py` - Tiered loading strategy
- `app/core/tool_cache.py` - Tool caching

### Individual Tools (Sample - there are many)
- `app/tools/visualization_maps_tools.py` - Map visualization tools
- `app/tools/complete_analysis_tools.py` - Complete analysis tools
- `app/tools/settlement_visualization_tools.py` - Settlement viz tools
- `app/tools/*.py` - Many more tool files

## Key Patterns to Change

### Current (PROBLEMATIC) Pattern:
```python
# Global singleton
_manager = None

def get_manager():
    global _manager
    if not _manager:
        _manager = Manager()
    return _manager

# Usage
manager = get_manager()
state = manager.get_state(session_id)  # Cached in memory
```

### Target (SAFE) Pattern:
```python
# No global state
@app.route('/endpoint')
def handle_request():
    user_id = validate_jwt_token(request.headers['Authorization'])
    session_id = request.json['session_id']

    # Validate ownership in database
    ownership = db.query(
        "SELECT 1 FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    ).fetchone()

    if not ownership:
        abort(403)

    # Load from disk/database, never cache
    data = load_from_storage(session_id)

    # Process
    result = process(data)

    # Save to database
    save_to_storage(session_id, result)

    return jsonify(result)
    # Nothing persists in memory after request
```

## Priority Files for Refactoring

### Phase 1 - Eliminate Memory State (URGENT)
1. `app/core/unified_data_state.py` - Remove singleton pattern
2. `app/core/analysis_state_handler.py` - Remove global instance
3. `app/core/tool_registry.py` - Make request-scoped
4. `app/core/tool_cache.py` - Eliminate caching
5. `app/core/request_interpreter.py` - Remove conversation history storage

### Phase 2 - Add Authentication Layer
1. `app/web/routes/core_routes.py` - Add user authentication
2. `app/web/routes/upload_routes.py` - Validate user owns session
3. `app/web/routes/analysis_routes.py` - Check user permissions
4. `app/auth/models.py` - Enhance user model
5. `app/core/decorators.py` - Add @require_authentication decorator

### Phase 3 - Database-Backed Sessions
1. `app/config/redis_config.py` - Ensure Redis is required
2. Create `app/models/session.py` - Database session model
3. Create `app/services/session_service.py` - Session management service
4. Update all routes to use database sessions

### Phase 4 - Stateless Workers
1. `gunicorn.conf.py` - Set `preload_app=False`
2. Remove all `global` variables from all files
3. Make all services request-scoped

## Files to Create (NEW)

1. `app/models/session.py` - Session database model
2. `app/services/session_service.py` - Centralized session management
3. `app/services/auth_service.py` - JWT/authentication service
4. `app/services/storage_service.py` - S3/cloud storage service
5. `app/middleware/auth_middleware.py` - Authentication middleware
6. `app/middleware/session_middleware.py` - Session validation middleware
7. `alembic/` - Database migration scripts

## Files to DELETE

1. All `*_singleton.py` patterns
2. Global state managers
3. In-memory caching layers
4. Worker-local state storage

## Configuration Changes Needed

1. **Environment Variables**:
   - Add `JWT_SECRET_KEY`
   - Add `DATABASE_URL` (PostgreSQL)
   - Add `S3_BUCKET_NAME`
   - Add `REDIS_URL` (required, no fallback)

2. **Database Schema**:
   - Users table
   - Sessions table
   - Files table
   - Analysis_results table

3. **Infrastructure**:
   - PostgreSQL database
   - Redis (required)
   - S3 bucket for files
   - Secrets manager for keys

## Testing Requirements

1. **Multi-user concurrency test**
2. **Session isolation verification**
3. **Worker restart resilience**
4. **Database transaction testing**
5. **Authentication flow testing**
6. **Rate limiting testing**

## Success Metrics

- Zero session bleed in 1000 concurrent user test
- All state in database or Redis
- No global variables in Python
- JWT authentication on all endpoints
- Database-enforced row-level security
- Stateless worker processes