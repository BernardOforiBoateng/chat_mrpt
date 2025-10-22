# Profile & Sign In/Out Implementation Plan

**Date**: 2025-09-30
**Status**: In Progress
**Approved**: Yes

---

## Implementation Strategy

### Phase 1: Frontend Infrastructure (Steps 1-4)
Add authentication state management and API services

### Phase 2: UI Components (Steps 5-7)
Build login/signup modals and profile section

### Phase 3: Integration & Testing (Steps 8-9)
Connect everything and test the flow

---

## Detailed Implementation Steps

### Step 1: User Authentication Store ✅ NEXT
**File**: `frontend/src/stores/userStore.ts`
**Purpose**: Zustand store for user authentication state

**Features**:
- User state (authenticated, user data)
- Login/logout actions
- Token management
- Persist to localStorage

**Dependencies**: None

---

### Step 2: Auth API Service ✅
**File**: `frontend/src/services/auth.ts`
**Purpose**: API calls for authentication

**Endpoints**:
- POST /auth/signin
- POST /auth/signup
- POST /auth/logout
- GET /auth/status

**Dependencies**: Step 1 (userStore)

---

### Step 3: User Avatar Component ✅
**File**: `frontend/src/components/Profile/UserAvatar.tsx`
**Purpose**: Display user avatar with initials or image

**Features**:
- Show initials if no avatar
- Colored background based on username
- Different sizes (small, medium, large)

**Dependencies**: None

---

### Step 4: Profile Section Component ✅
**File**: `frontend/src/components/Profile/ProfileSection.tsx`
**Purpose**: Profile display in sidebar

**Features**:
- User avatar
- Username & email
- Dropdown menu (Settings, Sign out)
- Sign in button when not authenticated

**Dependencies**: Step 1, 3

---

### Step 5: Login Modal Component ✅
**File**: `frontend/src/components/Auth/LoginModal.tsx`
**Purpose**: Login form modal

**Features**:
- Email & password inputs
- Form validation
- Error handling
- Link to signup
- Remember me option

**Dependencies**: Step 1, 2

---

### Step 6: Signup Modal Component ✅
**File**: `frontend/src/components/Auth/SignupModal.tsx`
**Purpose**: Registration form modal

**Features**:
- Email, username, password inputs
- Password strength indicator
- Form validation
- Error handling
- Link to login

**Dependencies**: Step 1, 2

---

### Step 7: Update Sidebar Component ✅
**File**: `frontend/src/components/Sidebar/Sidebar.tsx`
**Purpose**: Add profile section to existing sidebar

**Changes**:
- Add ProfileSection at top of sidebar
- Keep existing History/Samples sections
- Adjust layout for profile

**Dependencies**: Step 4

---

### Step 8: Testing ✅
**Tasks**:
- Test signup flow
- Test login flow
- Test logout flow
- Test session persistence
- Test error handling
- Test across browsers

---

### Step 9: Production Deployment ✅
**Tasks**:
- Build React app
- Deploy to both production instances
- Test on production
- Monitor for errors

---

## File Structure

```
frontend/src/
├── stores/
│   └── userStore.ts          # NEW - User auth state
├── services/
│   └── auth.ts               # NEW - Auth API calls
├── components/
│   ├── Profile/              # NEW FOLDER
│   │   ├── ProfileSection.tsx
│   │   └── UserAvatar.tsx
│   ├── Auth/                 # NEW FOLDER
│   │   ├── LoginModal.tsx
│   │   └── SignupModal.tsx
│   └── Sidebar/
│       └── Sidebar.tsx       # MODIFIED
```

---

## Design Specifications

### Profile Section Layout
```
┌─────────────────────────────┐
│  [Avatar] Username          │
│           user@email.com    │
│           [⚙️ ▼]            │
└─────────────────────────────┘

Dropdown Menu:
┌──────────────────┐
│ 👤 Profile       │
│ ⚙️  Settings     │
│ ─────────────    │
│ 🚪 Sign out      │
└──────────────────┘
```

### Avatar Colors
```typescript
// Based on username hash
const colors = [
  'bg-blue-500',
  'bg-green-500',
  'bg-purple-500',
  'bg-pink-500',
  'bg-indigo-500'
];
```

### Login Modal
```
┌─────────────────────────────┐
│  Welcome Back               │
│                             │
│  Email: [_______________]   │
│  Password: [___________]    │
│  □ Remember me              │
│                             │
│  [    Sign In    ]          │
│                             │
│  Don't have an account?     │
│  Sign up                    │
└─────────────────────────────┘
```

### Signup Modal
```
┌─────────────────────────────┐
│  Create Account             │
│                             │
│  Email: [_______________]   │
│  Username: [____________]   │
│  Password: [____________]   │
│  ████░░ Strength: Medium    │
│                             │
│  [    Sign Up    ]          │
│                             │
│  Already have an account?   │
│  Sign in                    │
└─────────────────────────────┘
```

---

## API Integration

### User State Shape
```typescript
interface User {
  id: string;
  email: string;
  username: string;
}

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}
```

### API Response Format
```typescript
// Login/Signup Success
{
  success: true,
  user: {
    id: "...",
    email: "...",
    username: "..."
  },
  token: "..."
}

// Login/Signup Error
{
  success: false,
  message: "Error message here"
}

// Status Check
{
  success: true,
  authenticated: true/false,
  user: { ... } | null
}
```

---

## Session Management

### Token Storage
- Store JWT in localStorage: `auth_token`
- Include in API requests: `Authorization: Bearer <token>`
- Auto-refresh on app load
- Clear on logout

### Session Persistence
- Check auth status on app mount
- Restore user state from token
- Handle expired tokens gracefully

---

## Error Handling

### Error Messages
```typescript
const errorMessages = {
  'Email already registered': 'This email is already in use',
  'Invalid email or password': 'Incorrect email or password',
  'Email and password are required': 'Please fill in all fields',
  'Network error': 'Connection failed. Please try again'
};
```

### Error Display
- Toast notifications for errors
- Inline validation for forms
- Clear error states on input change

---

## Security Considerations

1. **Password Requirements**:
   - Minimum 8 characters
   - At least one uppercase
   - At least one lowercase
   - At least one number

2. **Token Management**:
   - Store tokens in localStorage
   - Include in Authorization header
   - Clear on logout
   - Handle expiration

3. **Input Validation**:
   - Frontend validation
   - Backend validation (already exists)
   - Sanitize inputs

---

## Testing Checklist

### Functional Tests
- [ ] Signup with valid data
- [ ] Signup with existing email (should fail)
- [ ] Signup with weak password (should fail)
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should fail)
- [ ] Logout clears session
- [ ] Session persists on page refresh
- [ ] Token expires after 7 days
- [ ] Profile section shows user info
- [ ] Dropdown menu works

### UI Tests
- [ ] Modals open and close correctly
- [ ] Form validation shows errors
- [ ] Loading states display
- [ ] Avatar displays correctly
- [ ] Responsive on mobile
- [ ] Accessible (keyboard navigation)

### Integration Tests
- [ ] Login → session persists → logout
- [ ] Signup → auto-login → use app
- [ ] Multiple tabs stay synced
- [ ] Works across browser refresh

---

## Deployment Strategy

### Build Process
```bash
cd frontend
npm run build
```

### Deployment Script
```bash
# Copy to static folder
cp -r frontend/dist/* app/static/react/

# Deploy to production instances
./deploy_auth_ui.sh
```

### Production Deployment
1. Build React app locally
2. Copy to `app/static/react/`
3. Deploy to Instance 1 (3.21.167.170)
4. Deploy to Instance 2 (18.220.103.20)
5. Test on CloudFront URL
6. Monitor logs for errors

---

## Rollback Plan

If issues occur:
1. Revert Sidebar.tsx changes
2. Remove new components
3. Keep userStore (won't break anything)
4. Re-deploy previous build

---

## Success Criteria

✅ Users can sign up with email/username/password
✅ Users can log in with email/password
✅ Users can log out
✅ Profile section shows in sidebar
✅ Session persists across page refresh
✅ Works on both production instances
✅ No breaking changes to existing features

---

## Timeline

- **Step 1-2**: 30 minutes (Stores & Services)
- **Step 3-4**: 45 minutes (Avatar & Profile)
- **Step 5-6**: 60 minutes (Login/Signup Modals)
- **Step 7**: 30 minutes (Sidebar Update)
- **Step 8**: 45 minutes (Testing)
- **Step 9**: 30 minutes (Deployment)

**Total**: ~4 hours

---

**Status**: Ready to implement
**Next Step**: Create userStore.ts
