# SnapQuote Backend Fix - OAuth and Monitoring

## Issues Fixed

### 1. **OAuth Opens Automatically on Startup** ❌ → ✅
**Problem**: When backend starts, it immediately opens OAuth browser window even without frontend interaction.

**Root Cause**: The `start_gmail_monitoring()` function was called on startup and immediately tried to authenticate.

**Solution**:
- Removed automatic authentication on startup
- OAuth now only triggers when frontend calls `/api/auth/login`
- Added smart token checking to start monitoring if valid token exists

---

### 2. **Email Monitoring Loop Not Running** ❌ → ✅
**Problem**: Email monitoring thread never starts after authentication.

**Root Cause**: Monitoring was tied to the old startup flow which didn't complete properly.

**Solution**:
- Monitoring now starts automatically after successful authentication via `/api/auth/login`
- Uses a background daemon thread
- Global service instance maintained for monitoring control

---

## Technical Changes

### app.py

#### Added Global State Management
```python
# Global Gmail service instance
gmail_service_instance = None
monitoring_active = False
```

#### Updated `/api/auth/login` Endpoint
- Now stores authenticated service instance globally
- Starts monitoring thread automatically after authentication
- Monitoring runs in background daemon thread

#### Updated `/api/auth/logout` Endpoint
- Stops monitoring when user logs out
- Cleans up global service instance
- Removes token file

#### New Function: `start_monitoring_loop(gmail_service)`
- Background thread function for email monitoring
- Runs continuously checking for new emails
- Logs monitoring activity

#### New Function: `initialize_database()`
- Separates database initialization from monitoring
- Runs on startup regardless of authentication

#### New Function: `check_and_start_monitoring_if_authenticated()`
- Checks if token.json exists on startup
- Validates and refreshes token if needed
- Automatically starts monitoring if token is valid
- User doesn't need to login again if already authenticated

#### Updated `main()` Function
- Removes automatic monitoring thread
- Only initializes database
- Checks for existing authentication and starts monitoring if valid
- Shows appropriate messages based on authentication state

---

### gmail_service.py

#### Added Helper Method: `_build_service()`
```python
def _build_service(self):
    """Build Gmail API service from credentials."""
    if self.credentials:
        service = build('gmail', 'v1', credentials=self.credentials)
        self._initialize_labels()
        return service
```

**Purpose**: Allows building Gmail service from existing credentials without full re-authentication.

---

## New Behavior Flow

### Case 1: Fresh Start (No token.json)

```
1. Backend starts
   └─ Database initialized ✅
   └─ No token found
   └─ Message: "Please login via frontend"
   └─ API server ready

2. User opens frontend (http://localhost:5173/)
   └─ Frontend checks /api/auth/status
   └─ Response: authenticated = false
   └─ Shows login page

3. User clicks "Continue with Google"
   └─ Frontend calls /api/auth/login
   └─ Backend opens OAuth browser window
   └─ User grants permissions
   └─ Token saved to token.json
   └─ Monitoring thread starts automatically ✅
   └─ Response: success = true
   └─ Frontend redirects to /dashboard

4. Dashboard loads
   └─ Emails being monitored every 30 seconds ✅
   └─ New emails processed automatically ✅
```

---

### Case 2: Restart with Existing Token

```
1. Backend starts
   └─ Database initialized ✅
   └─ Token found (token.json exists)
   └─ Token validated ✅
   └─ Monitoring starts automatically ✅
   └─ Message: "Email monitoring active"
   └─ API server ready

2. User opens frontend
   └─ Frontend checks /api/auth/status
   └─ Response: authenticated = true ✅
   └─ Auto-redirects to /dashboard

3. Dashboard loads
   └─ Shows existing emails ✅
   └─ Monitoring already active ✅
```

---

### Case 3: Expired Token on Restart

```
1. Backend starts
   └─ Database initialized ✅
   └─ Token found but expired
   └─ Attempts to refresh token
   
   Case 3a: Refresh Successful
   └─ Token refreshed ✅
   └─ Monitoring starts ✅
   └─ Message: "Token refreshed successfully"
   
   Case 3b: Refresh Failed
   └─ Message: "Please login via frontend to re-authenticate"
   └─ User must login again via frontend
```

---

### Case 4: User Logout

```
1. User clicks logout (if implemented in frontend)
   └─ Frontend calls POST /api/auth/logout
   └─ Backend stops monitoring ✅
   └─ Token file deleted ✅
   └─ Global service cleared ✅
   └─ Frontend redirects to /

2. User must re-authenticate to access dashboard
```

---

## Console Output Examples

### Fresh Start (No Token)
```
🚀 Starting SnapQuote Gmail Monitor with API...
✅ Configuration validated
🗄️ Initializing DuckDB database...
✅ DuckDB database ready
💡 No authentication token found. Please login via frontend.
🌐 Starting Flask API server...
📡 API Endpoints available:
   GET /api/auth/status - Check authentication status
   GET /api/auth/login - Login with Google
   POST /api/auth/logout - Logout
   ...
🚀 Server running at http://localhost:5000
============================================================
💡 Tip: Email monitoring will start automatically when you login via frontend
============================================================
```

### After Frontend Login
```
[Frontend calls /api/auth/login]
📧 Email monitoring started
📧 Starting email monitoring (checking every 30 seconds)
📱 Monitoring active - new emails will be processed automatically
============================================================
```

### Restart with Valid Token
```
🚀 Starting SnapQuote Gmail Monitor with API...
✅ Configuration validated
🗄️ Initializing DuckDB database...
✅ DuckDB database ready
🔍 Found existing authentication token...
✅ Token is valid, starting email monitoring...
📧 Email monitoring active
🌐 Starting Flask API server...
📡 API Endpoints available:
   ...
🚀 Server running at http://localhost:5000
============================================================
[No "Please login" message - already authenticated]
```

---

## Testing Steps

### Test 1: Fresh Authentication
```bash
# 1. Delete token.json
rm token.json

# 2. Start backend
python app.py

# Expected: No OAuth window opens
# Expected: "Please login via frontend" message

# 3. Open frontend
# http://localhost:5173/

# Expected: Shows login page

# 4. Click "Continue with Google"
# Expected: OAuth window opens
# Expected: After granting permissions, redirected to dashboard
# Expected: Backend logs show "Email monitoring started"
```

### Test 2: Restart with Token
```bash
# 1. Backend already authenticated (token.json exists)
# 2. Restart backend
python app.py

# Expected: No OAuth window
# Expected: "Email monitoring active" message
# Expected: Monitoring already running

# 3. Open frontend
# Expected: Auto-redirected to dashboard (no login page)
```

### Test 3: Send Test Email
```bash
# With monitoring active, send email to your Gmail

# Expected within 30 seconds:
# - Backend logs show email processing
# - Dashboard updates with new email (after refresh)
```

---

## API Endpoint Changes

### `/api/auth/login`
**Before**: Only authenticated, didn't start monitoring
**After**: Authenticates AND starts monitoring thread

### `/api/auth/logout` (NEW behavior)
**Before**: Only deleted token
**After**: Deletes token AND stops monitoring

### `/api/auth/status`
**No Change**: Still checks if token exists and is valid

---

## Files Modified

1. **app.py**
   - Added global state variables
   - Refactored authentication flow
   - Added monitoring control
   - New helper functions

2. **gmail_service.py**
   - Added `_build_service()` method
   - Allows service creation from existing credentials

---

## Monitoring Control Flow

```
┌─────────────────────────────────────────────────┐
│           Backend Startup                        │
├─────────────────────────────────────────────────┤
│ 1. Initialize Database                          │
│ 2. Check for existing token.json               │
│    ├─ If valid → Start monitoring immediately  │
│    └─ If not → Wait for frontend login         │
│ 3. Start Flask API server                      │
└─────────────────────────────────────────────────┘
                     │
                     ├─ Token Exists & Valid
                     │  └─→ Monitoring Thread Running ✅
                     │
                     └─ No Token / Invalid
                        └─→ Wait for /api/auth/login
                           └─→ OAuth Flow
                              └─→ Monitoring Thread Starts ✅
```

---

## Benefits of New Approach

✅ **No Unexpected OAuth Windows**: Only opens when user explicitly clicks login

✅ **Automatic Monitoring**: Starts as soon as authentication succeeds

✅ **Persistent Sessions**: Token persists across restarts, no re-login needed

✅ **Smart Token Refresh**: Automatically refreshes expired tokens

✅ **Clean Logout**: Properly stops monitoring and cleans up

✅ **Better UX**: Frontend controls authentication flow completely

✅ **Production Ready**: Monitoring runs reliably in background

---

## Environment Requirements

- Python 3.8+
- Flask with CORS
- Google OAuth credentials (credentials.json)
- Gmail API enabled in Google Cloud Console

---

## Troubleshooting

### Issue: Monitoring not starting after login
**Check**: Backend logs for "Email monitoring started" message
**Solution**: Verify gmail_service.authenticate() returns True

### Issue: Token refresh fails
**Check**: credentials.json has correct client_id and client_secret
**Solution**: Delete token.json and re-authenticate

### Issue: OAuth window opens on startup
**Check**: You're running the fixed version of app.py
**Solution**: Verify start_gmail_monitoring() is NOT called in main()

---

## Summary

The backend now properly separates authentication from monitoring, only initiates OAuth when the frontend requests it, and automatically manages monitoring state. The user experience is much cleaner with no unexpected OAuth windows on backend startup.

✅ **All Fixed!**
