# ChatMRPT React Migration Plan

## Executive Summary
This document outlines a comprehensive strategy for migrating ChatMRPT from its current HTML/CSS/Vanilla JavaScript architecture to React.js. The migration will modernize the frontend while maintaining all existing functionality and API compatibility.

## Current Architecture Analysis

### Frontend Stack
- **Templates**: 29 HTML templates using Jinja2 templating
- **JavaScript**: Modular ES6 architecture with 12 JS modules
- **Styling**: Tailwind CSS (modern-minimalist-theme.css)
- **Libraries**: Bootstrap 5.3.2 (modals only), Font Awesome 6.4.2

### Key Frontend Components
1. **Main Application** (`index.html`)
   - Chat interface
   - Sidebar settings
   - File upload modals
   - Report generation modal
   - Visualization modal

2. **JavaScript Modules**
   - `chat-manager-refactored.js` - Main chat orchestration
   - `message-handler.js` - Message processing
   - `visualization-manager.js` - Visualization handling
   - `api-client.js` - Backend communication
   - `file-uploader.js` - File upload management
   - `data-upload-manager.js` - Data management
   - `sidebar.js` - Settings sidebar
   - Various utility modules

3. **Admin Interface** (`/admin/*`)
   - Dashboard with analytics
   - Session management
   - Log viewing
   - System health monitoring

### Backend API Endpoints

#### Core Endpoints
- `GET /` - Main application
- `GET /session_info` - Session state
- `POST /clear_session` - Reset session
- `GET /app_status` - Application health

#### Chat & Analysis
- `POST /send_message` - Chat messages (non-streaming)
- `POST /send_message_streaming` - Chat messages (streaming)
- `POST /run_analysis` - Direct analysis execution
- `GET /explain_variable_selection` - Variable explanations

#### File Management
- `POST /upload_both_files` - CSV/Shapefile upload
- `POST /load_sample_data` - Load demo data
- `GET /api/tpr/detect-states` - TPR state detection
- `POST /api/tpr/process` - TPR processing
- `GET /api/download/*` - File downloads

#### Visualization & Reports
- `POST /get_visualization` - Generate visualizations
- `POST /navigate_*` - Pagination for visualizations
- `GET /serve_viz_file/*` - Serve visualization files
- `POST /generate_report` - Generate reports
- `GET /download_report/*` - Download reports

#### Data API
- `GET /api/variables` - Available variables
- `GET /api/variable_metadata` - Variable metadata
- `GET /api/wards` - Ward information

## React Migration Strategy

### Phase 1: Setup & Infrastructure (Week 1-2)

1. **Project Setup**
   ```bash
   # Create React app with TypeScript
   npx create-react-app chatmrpt-react --template typescript
   
   # Install core dependencies
   npm install axios react-router-dom @tanstack/react-query
   npm install tailwindcss @headlessui/react @heroicons/react
   npm install react-markdown recharts leaflet react-leaflet
   npm install socket.io-client # For streaming support
   ```

2. **Development Environment**
   - Setup proxy in package.json for Flask backend
   - Configure TypeScript for strict mode
   - Setup ESLint and Prettier
   - Configure Tailwind CSS

3. **Project Structure**
   ```
   src/
   ├── components/
   │   ├── chat/
   │   │   ├── ChatContainer.tsx
   │   │   ├── MessageList.tsx
   │   │   ├── MessageInput.tsx
   │   │   └── StreamingMessage.tsx
   │   ├── upload/
   │   │   ├── FileUploadModal.tsx
   │   │   ├── TPRUpload.tsx
   │   │   └── StandardUpload.tsx
   │   ├── visualization/
   │   │   ├── VisualizationModal.tsx
   │   │   ├── MapVisualization.tsx
   │   │   └── ChartVisualization.tsx
   │   ├── layout/
   │   │   ├── Header.tsx
   │   │   ├── Sidebar.tsx
   │   │   └── Layout.tsx
   │   └── common/
   │       ├── Button.tsx
   │       ├── Modal.tsx
   │       └── LoadingSpinner.tsx
   ├── pages/
   │   ├── Home.tsx
   │   ├── Admin.tsx
   │   └── ReportBuilder.tsx
   ├── services/
   │   ├── api.ts
   │   ├── chatService.ts
   │   ├── uploadService.ts
   │   └── visualizationService.ts
   ├── hooks/
   │   ├── useChat.ts
   │   ├── useSession.ts
   │   ├── useFileUpload.ts
   │   └── useVisualization.ts
   ├── store/
   │   ├── sessionStore.ts
   │   ├── chatStore.ts
   │   └── dataStore.ts
   └── utils/
       ├── constants.ts
       ├── helpers.ts
       └── types.ts
   ```

### Phase 2: Core Components Migration (Week 3-4)

1. **State Management**
   - Use React Context + useReducer for global state
   - Implement session management
   - Port conversation history handling
   - Migrate theme management

2. **Chat System**
   - Build ChatContainer component
   - Implement streaming message support
   - Port message formatting and rendering
   - Add markdown support
   - Handle clarification flows

3. **API Integration**
   - Create axios-based API client
   - Implement request/response interceptors
   - Add error handling
   - Setup React Query for caching

### Phase 3: Feature Components (Week 5-6)

1. **File Upload System**
   - Port file upload modal
   - Implement drag-and-drop
   - Add progress indicators
   - Handle TPR uploads
   - Maintain state detection logic

2. **Visualization System**
   - Create visualization modal
   - Integrate Leaflet for maps
   - Use Recharts for charts
   - Implement pagination
   - Add export functionality

3. **Analysis Workflow**
   - Port method selection
   - Variable selection UI
   - Progress indicators
   - Result display

### Phase 4: Admin Interface (Week 7)

1. **Admin Dashboard**
   - Create admin route protection
   - Port dashboard components
   - Implement session analytics
   - Add log viewer
   - System health monitoring

2. **Report Builder**
   - Port report builder interface
   - Add preview functionality
   - Implement format selection

### Phase 5: Integration & Testing (Week 8)

1. **Backend Integration**
   - Update CORS settings
   - Modify session handling
   - Test all API endpoints
   - Ensure authentication works

2. **Testing**
   - Unit tests with Jest
   - Integration tests
   - E2E tests with Cypress
   - Performance testing

### Phase 6: Deployment (Week 9)

1. **Build Process**
   - Setup production build
   - Optimize bundle size
   - Configure environment variables
   - Setup CI/CD

2. **Deployment Options**
   - Option A: Serve React build via Flask
   - Option B: Separate frontend deployment (Vercel/Netlify)
   - Option C: Docker containerization

## Component Mapping

### Current → React Components

| Current File | React Component | Notes |
|-------------|-----------------|-------|
| index.html | Layout.tsx + Home.tsx | Main application shell |
| chat-manager-refactored.js | ChatContainer.tsx + useChat.ts | Chat orchestration |
| message-handler.js | MessageList.tsx + MessageInput.tsx | Message handling |
| visualization-manager.js | VisualizationModal.tsx | Visualization display |
| file-uploader.js | FileUploadModal.tsx | File upload UI |
| api-client.js | services/api.ts | API communication |
| sidebar.js | Sidebar.tsx | Settings panel |
| admin templates | Admin.tsx + sub-components | Admin interface |

## Key Considerations

### 1. Streaming Support
- Implement Server-Sent Events (SSE) handling
- Use React state for progressive rendering
- Maintain message buffering logic

### 2. Session Management
- Port Flask session to React state
- Use localStorage for persistence
- Implement session recovery

### 3. File Handling
- Maintain current upload logic
- Add progress tracking
- Implement chunked uploads for large files

### 4. Visualization Integration
- Keep current backend visualization generation
- React to display generated HTML/images
- Consider D3.js for interactive charts

### 5. Authentication
- Maintain Flask-Login for admin
- Add JWT tokens for API calls
- Implement protected routes

## Migration Benefits

1. **Improved Performance**
   - Virtual DOM for efficient updates
   - Code splitting and lazy loading
   - Better state management

2. **Better Developer Experience**
   - Component reusability
   - TypeScript type safety
   - Modern tooling

3. **Enhanced User Experience**
   - Smoother interactions
   - Better loading states
   - Improved error handling

4. **Maintainability**
   - Clear component structure
   - Easier testing
   - Better documentation

## Risk Mitigation

1. **Gradual Migration**
   - Start with non-critical components
   - Maintain parallel systems initially
   - Feature flag new components

2. **API Compatibility**
   - Keep existing endpoints
   - Version new endpoints
   - Maintain backward compatibility

3. **Testing Strategy**
   - Comprehensive test coverage
   - User acceptance testing
   - Performance benchmarking

## Timeline Summary

- **Weeks 1-2**: Setup and infrastructure
- **Weeks 3-4**: Core components
- **Weeks 5-6**: Feature components
- **Week 7**: Admin interface
- **Week 8**: Integration and testing
- **Week 9**: Deployment

Total estimated time: 9 weeks for complete migration

## Next Steps

1. Get stakeholder approval
2. Setup development environment
3. Create proof of concept for chat component
4. Begin incremental migration
5. Regular progress reviews

This migration plan provides a clear path forward while minimizing disruption to the existing system. The modular approach allows for flexibility and risk mitigation throughout the process.