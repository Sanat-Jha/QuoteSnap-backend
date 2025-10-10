# SnapQuote Backend-Frontend Integration Guide

## Overview
This document describes the complete integration between the SnapQuote Flask backend and the React frontend (DashB).

## Architecture

### Backend: Flask API (Port 5000)
- **Location**: `c:\Users\sanat\Desktop\SnapQuote\backend\`
- **Framework**: Flask with CORS enabled
- **Database**: DuckDB (local file-based)
- **Authentication**: Google OAuth 2.0 (Gmail API)

### Frontend: React Application (Port 5173)
- **Location**: `c:\Users\sanat\Desktop\SnapQuote\backend\DashB\`
- **Framework**: React with Vite
- **UI Library**: Tailwind CSS + Framer Motion
- **Routing**: React Router

---

## API Endpoints

### Authentication Endpoints

#### `GET /api/auth/status`
**Purpose**: Check if user is authenticated with Google OAuth

**Response**:
```json
{
  "authenticated": true/false,
  "message": "Status message"
}
```

**Usage in Frontend**: Called on app mount and before accessing protected routes

---

#### `GET /api/auth/login`
**Purpose**: Initiate Google OAuth flow for Gmail API access

**Response**:
```json
{
  "success": true,
  "message": "Authentication successful",
  "redirect": "http://localhost:5173/dashboard"
}
```

**Flow**:
1. User clicks "Continue with Google" button
2. Frontend calls this endpoint
3. Backend opens browser window for Google OAuth
4. User grants permissions
5. Token saved to `token.json`
6. Frontend redirects to dashboard

---

#### `POST /api/auth/logout`
**Purpose**: Logout user by removing OAuth token

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### Email Data Endpoints

#### `GET /api/emails`
**Purpose**: Fetch all processed emails with extraction data

**Response**:
```json
{
  "success": true,
  "count": 10,
  "table_count": 10,
  "data": [
    {
      "id": 1,
      "gmail_id": "abc123",
      "subject": "Hardware Inquiry",
      "sender": "john@example.com",
      "received_at": "2025-10-10T10:30:00",
      "extraction_status": "VALID",
      "extraction_result": {
        "to": "John Doe",
        "email": "john@example.com",
        "mobile": "+1234567890",
        "Requirements": [
          "10 x Screwdrivers",
          "5 x Hammer sets"
        ]
      }
    }
  ]
}
```

**Usage**: Dashboard fetches this data on mount to display email list

---

#### `GET /api/emails/stats`
**Purpose**: Get email processing statistics

**Response**:
```json
{
  "success": true,
  "stats": {
    "total_emails": 50,
    "valid_quotations": 35,
    "irrelevant_emails": 15
  }
}
```

**Usage**: Dashboard displays these stats in the stats cards

---

#### `GET /api/quotation/generate/<gmail_id>`
**Purpose**: Generate and download Excel quotation file for a specific email

**Parameters**:
- `gmail_id` (path): Gmail message ID

**Response**: Excel file download (in-memory generation, no local storage)

**Filename Format**: `Quotation_<subject>_<timestamp>.xlsx`

**Usage**: Download button in dashboard triggers this endpoint

**Features**:
- Generates Excel from template (`sample/QuotationFormat.xlsx`)
- Fills client info (name, email, phone)
- Populates requirements/items table
- Returns file directly from memory (no disk storage)
- Only works for emails with `extraction_status = "VALID"`

---

### Debug Endpoints

#### `GET /api/debug/database`
**Purpose**: Debug database status and content

**Response**: Database schema, tables, sample data

---

#### `GET /api/health`
**Purpose**: Health check endpoint

**Response**:
```json
{
  "success": true,
  "message": "SnapQuote API is running",
  "timestamp": "2025-10-10T10:30:00"
}
```

---

## Frontend Components

### App.jsx (Login Page - `/`)
**Features**:
- Beautiful animated login page
- "Continue with Google" button
- Authentication status check on mount
- Auto-redirect to dashboard if already authenticated
- Error handling for authentication failures
- Loading states during OAuth flow

**Key Functions**:
```javascript
checkAuthStatus()  // Checks if user is authenticated
handleLogin()      // Initiates OAuth flow
```

---

### Dashboard.jsx (`/dashboard`)
**Features**:
- Protected route with authentication guard
- Real-time email data display
- Statistics cards (Total, Valid, Irrelevant)
- Email table with:
  - Email address
  - Client name
  - Requirements popup
  - Status badge
  - Download button (only for processed emails)
- Loading and error states
- Auto-refresh capability

**Key Functions**:
```javascript
checkAuthAndFetchData()  // Verify auth and fetch data
fetchEmails()            // Get all emails from API
fetchStats()             // Get statistics
handleDownload()         // Trigger Excel download
```

**Data Transformation**:
- API data is transformed to match UI structure
- Requirements array extracted from `extraction_result`
- Status mapped: `VALID` → `Processed`, others → `Pending`

---

## Authentication Flow

### Initial Login
```
1. User opens http://localhost:5173/
2. Frontend checks /api/auth/status
3. If not authenticated, show login page
4. User clicks "Continue with Google"
5. Frontend calls /api/auth/login
6. Backend opens browser for Google OAuth
7. User grants Gmail permissions
8. Backend saves token to token.json
9. Backend monitoring thread starts
10. Frontend redirects to /dashboard
```

### Accessing Dashboard
```
1. User navigates to /dashboard
2. Dashboard checks /api/auth/status
3. If not authenticated → redirect to /
4. If authenticated → fetch emails and stats
5. Display data in table
```

### Token Refresh
```
- Backend automatically refreshes expired tokens
- Uses refresh_token from stored credentials
- No user interaction needed
- Happens transparently on /api/auth/status check
```

---

## Email Processing Pipeline

### Backend Process
```
1. Gmail monitoring thread checks for new emails (every 30s)
2. New email detected
3. Email content extracted (including attachments)
4. AI extraction service processes content:
   - Identifies if it's a quotation request
   - Extracts client info (name, email, phone)
   - Extracts requirements list
   - Determines validity (VALID/IRRELEVANT)
5. Data saved to DuckDB database
6. Frontend can now fetch and display the email
```

### Frontend Display
```
1. Dashboard fetches /api/emails
2. Transforms API data to UI format
3. Displays in table with:
   - Client email and name
   - Requirements (popup view)
   - Status badge
   - Download button (for VALID emails only)
```

---

## Excel Generation Flow

### Download Process
```
1. User clicks Download button for a valid email
2. Frontend calls /api/quotation/generate/<gmail_id>
3. Backend:
   - Loads template (QuotationFormat.xlsx)
   - Fills client information
   - Populates requirements table
   - Saves to BytesIO (memory)
   - Returns file stream
4. Browser triggers download
5. File saved with descriptive name
```

### Template Structure
- Client Name: B2:C2 (merged)
- Client Email: B3:C3 (merged)
- Client Phone: B4:C4 (merged)
- Requirements: Starting from row 12
  - Column B: Description
  - Column C: Brand/Model
  - Column F: Quantity
  - Column G: Unit
  - Column H: Unit Price
  - Column I: Total Price

---

## Configuration

### Backend (`config/settings.py`)
```python
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE = "token.json"
EMAIL_CHECK_INTERVAL = 30  # seconds
```

### Frontend (API Base URL)
```javascript
const API_BASE_URL = 'http://localhost:5000';
```

### CORS Configuration
```python
CORS(app, supports_credentials=True, 
     origins=['http://localhost:5173', 'http://localhost:3000'])
```

---

## Running the Application

### Backend
```bash
cd c:\Users\sanat\Desktop\SnapQuote\backend
python app.py
```

**Output**:
```
🚀 Starting SnapQuote Gmail Monitor with API...
✅ Configuration validated
🗄️ Initializing DuckDB database...
✅ DuckDB database ready
🔐 Authenticating with Gmail...
✅ Gmail authentication successful
📧 Starting email monitoring (checking every 30 seconds)
🌐 Starting Flask API server...
📡 API Endpoints available:
   GET /api/emails - Get all stored emails
   GET /api/emails/stats - Get email statistics
   GET /api/health - Health check
🚀 Server running at http://localhost:5000
```

### Frontend
```bash
cd c:\Users\sanat\Desktop\SnapQuote\backend\DashB
npm install  # First time only
npm run dev
```

**Output**:
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## File Structure

```
backend/
├── app.py                          # Main Flask application
├── credentials.json                # Google OAuth credentials
├── token.json                     # OAuth access token (auto-generated)
├── requirements.txt               # Python dependencies
├── app/
│   └── services/
│       ├── gmail_service.py       # Gmail API integration
│       ├── duckdb_service.py      # Database operations
│       ├── excel_generation_service.py  # Excel generation
│       └── ai_email_extraction.py # AI extraction service
├── config/
│   └── settings.py                # Configuration
├── database/
│   └── snapquote.duckdb          # DuckDB database file
├── sample/
│   └── QuotationFormat.xlsx      # Excel template
└── DashB/                         # Frontend React app
    ├── src/
    │   ├── App.jsx               # Login page
    │   ├── Dashboard.jsx         # Dashboard page
    │   ├── main.jsx             # React entry point
    │   └── assets/
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## Key Features

### ✅ Implemented Features
1. **Google OAuth Authentication**
   - Seamless OAuth flow
   - Token refresh handling
   - Protected routes

2. **Real-time Email Monitoring**
   - Automatic email checking (30s interval)
   - Background thread monitoring
   - No polling from frontend

3. **AI-Powered Extraction**
   - Hardware quotation detection
   - Client information extraction
   - Requirements parsing

4. **Dynamic Dashboard**
   - Real-time statistics
   - Email list with full details
   - Requirements popup view
   - Status indicators

5. **Excel Generation**
   - In-memory generation (no disk storage)
   - Template-based formatting
   - Instant download
   - Clean filenames

6. **Error Handling**
   - Loading states
   - Error messages
   - Retry functionality
   - Graceful degradation

---

## Security Considerations

### Authentication
- OAuth 2.0 flow with Google
- Tokens stored securely in `token.json`
- CORS restricted to specific origins
- Session management with Flask

### File Security
- Download endpoint validates gmail_id
- Only VALID emails can be downloaded
- No directory traversal vulnerabilities
- In-memory Excel generation (no temp files)

---

## Troubleshooting

### Backend won't start
- Check if port 5000 is available
- Verify `credentials.json` exists
- Check Python dependencies installed

### Frontend can't connect
- Verify backend is running on port 5000
- Check CORS configuration
- Verify API_BASE_URL in frontend

### OAuth not working
- Check Google Cloud Console credentials
- Verify redirect URIs configured
- Delete `token.json` and re-authenticate

### No emails showing
- Check if Gmail monitoring is active
- Verify DuckDB database exists
- Check `/api/debug/database` endpoint

### Download not working
- Verify email has `extraction_status = "VALID"`
- Check Excel template exists at `sample/QuotationFormat.xlsx`
- Check browser popup blocker

---

## Future Enhancements

### Settings Panel (Currently Disabled)
- Monitoring interval configuration
- AI model selection
- Email filters
- Notification preferences

### Additional Features
- Email search and filtering
- Bulk download
- Custom templates
- Email reply automation
- Analytics dashboard

---

## API Testing

### Using cURL

**Check Auth Status:**
```bash
curl http://localhost:5000/api/auth/status
```

**Get Emails:**
```bash
curl http://localhost:5000/api/emails
```

**Get Stats:**
```bash
curl http://localhost:5000/api/emails/stats
```

**Download Quotation:**
```bash
curl -O http://localhost:5000/api/quotation/generate/<gmail_id>
```

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

---

## Dependencies

### Backend
```
flask
flask-cors
google-auth
google-auth-oauthlib
google-api-python-client
duckdb
openpyxl
python-dotenv
```

### Frontend
```
react
react-dom
react-router-dom
framer-motion
react-icons
tailwindcss
vite
```

---

## Contact & Support

For issues or questions:
1. Check this integration guide
2. Review error logs in terminal
3. Check browser console for frontend errors
4. Verify API endpoints with cURL

---

## Summary

✅ **Complete Integration Achieved**
- Backend serving API on port 5000
- Frontend running on port 5173
- OAuth authentication working
- Real data display in dashboard
- Excel download functionality
- Error handling and loading states
- Clean, production-ready code

🚀 **Ready for Use!**
