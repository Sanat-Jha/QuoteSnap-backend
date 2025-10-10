# SnapQuote Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ installed
- Node.js 18+ installed
- Google Cloud Project with Gmail API enabled
- `credentials.json` file from Google Cloud Console

---

## 📦 Installation

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd c:\Users\sanat\Desktop\SnapQuote\backend

# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Ensure you have credentials.json in the backend directory
# Get it from: https://console.cloud.google.com/
```

### 2. Frontend Setup

```powershell
# Navigate to frontend directory
cd c:\Users\sanat\Desktop\SnapQuote\backend\DashB

# Install dependencies (first time only)
npm install
```

---

## ▶️ Running the Application

### Step 1: Start Backend (Terminal 1)

```powershell
cd c:\Users\sanat\Desktop\SnapQuote\backend
python app.py
```

**Expected Output:**
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

### Step 2: Start Frontend (Terminal 2)

```powershell
cd c:\Users\sanat\Desktop\SnapQuote\backend\DashB
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 3: Access the Application

1. Open browser: http://localhost:5173/
2. Click "Continue with Google"
3. Authorize Gmail access in the popup window
4. You'll be redirected to the dashboard
5. View your emails and download quotations!

---

## 🎯 First Time OAuth Setup

When you click "Continue with Google" for the first time:

1. **Browser popup opens** with Google OAuth consent screen
2. **Select your Google account**
3. **Grant permissions** for Gmail access:
   - Read email messages
   - Modify email labels
4. **Popup closes automatically**
5. **Token saved** to `token.json` in backend directory
6. **Redirected to dashboard**

> **Note**: You only need to do this once. The token is saved for future sessions.

---

## 📧 Testing Email Monitoring

### Send a Test Email

Send an email to your Gmail account with hardware quotation request:

**Example Email:**
```
Subject: Hardware Quotation Request

Hi,

I need a quotation for the following items:

- 10 x Professional Screwdriver Set
- 5 x Adjustable Wrench (10-inch)
- 20 x Safety Goggles

Please provide pricing and availability.

Thank you,
John Doe
john.doe@example.com
+1-555-0123
```

### Check the Dashboard

1. Wait ~30 seconds for monitoring cycle
2. Refresh dashboard (or it auto-updates)
3. See new email in the table
4. Click "View Requirements" to see extracted items
5. Click "Download" to generate Excel quotation

---

## 🛠️ Common Issues & Solutions

### Issue: Backend won't start
```
Error: Port 5000 is already in use
```
**Solution**: 
- Stop any other application using port 5000
- Or change port in `app.py` (line ~350)

### Issue: Frontend can't connect to backend
```
Error: Failed to connect to the server
```
**Solution**:
- Verify backend is running on http://localhost:5000
- Check if CORS is enabled
- Try: `curl http://localhost:5000/api/health`

### Issue: OAuth popup blocked
```
Browser: Popup blocked by browser settings
```
**Solution**:
- Allow popups for localhost
- Chrome: Click popup icon in address bar
- Manually navigate to OAuth URL shown in terminal

### Issue: No emails showing in dashboard
```
Dashboard shows "No emails found"
```
**Solution**:
- Send a test email to your Gmail
- Wait 30 seconds for monitoring cycle
- Check backend terminal for processing logs
- Visit: http://localhost:5000/api/emails directly

### Issue: Download button disabled
```
Download button is grayed out
```
**Solution**:
- Button only works for emails with status "Processed"
- Check if email extraction was successful
- Irrelevant emails cannot be downloaded

### Issue: Excel template not found
```
Error: Template file not found
```
**Solution**:
- Ensure `sample/QuotationFormat.xlsx` exists
- Check file path in `excel_generation_service.py`

---

## 📊 Dashboard Features

### Statistics Cards
- **Total Emails**: All emails processed
- **Valid Quotations**: Emails identified as quotation requests
- **Irrelevant**: Non-quotation emails

### Email Table
- **Email**: Client's email address
- **Name**: Extracted client name
- **Requirements**: Click "View" to see popup with all items
- **Status**: 
  - 🟢 **Processed**: Valid quotation, can download
  - 🟡 **Pending**: Still processing or irrelevant
- **Actions**: Download Excel quotation

### Download Feature
- Generates Excel from template
- Fills client information automatically
- Lists all requirements
- Downloads with descriptive filename
- No files saved on server (memory-only)

---

## 🔄 Stopping the Application

### Stop Backend (Terminal 1)
```
Press Ctrl+C
```

### Stop Frontend (Terminal 2)
```
Press Ctrl+C
```

---

## 🧪 API Testing (Optional)

Test backend endpoints directly:

```powershell
# Health check
curl http://localhost:5000/api/health

# Get authentication status
curl http://localhost:5000/api/auth/status

# Get all emails
curl http://localhost:5000/api/emails

# Get statistics
curl http://localhost:5000/api/emails/stats

# Debug database
curl http://localhost:5000/api/debug/database
```

---

## 📁 Important Files

### Backend
- `app.py` - Main Flask application
- `credentials.json` - Google OAuth credentials (required)
- `token.json` - OAuth token (auto-generated on first login)
- `database/snapquote.duckdb` - Database file
- `sample/QuotationFormat.xlsx` - Excel template

### Frontend
- `src/App.jsx` - Login page
- `src/Dashboard.jsx` - Main dashboard
- `src/main.jsx` - React entry point

---

## 🔐 Security Notes

- `credentials.json` - Keep this file secure, don't commit to Git
- `token.json` - Contains access token, auto-generated, don't share
- OAuth tokens are refreshed automatically
- CORS is configured for localhost only

---

## 📖 Additional Resources

- **Full Integration Guide**: See `INTEGRATION_GUIDE.md`
- **Gmail API Docs**: https://developers.google.com/gmail/api
- **React Router**: https://reactrouter.com/
- **Flask CORS**: https://flask-cors.readthedocs.io/

---

## ✅ Success Checklist

- [ ] Backend running on port 5000
- [ ] Frontend running on port 5173
- [ ] OAuth authentication completed
- [ ] Token saved to `token.json`
- [ ] Dashboard loads successfully
- [ ] Emails displayed in table
- [ ] Download button works
- [ ] Excel file downloads correctly

---

## 🎉 You're All Set!

Your SnapQuote application is now fully integrated and running!

**Next Steps:**
1. Send test emails to your Gmail
2. Monitor the dashboard for new entries
3. Download quotations as Excel files
4. Customize the Excel template if needed

**Need Help?**
- Check `INTEGRATION_GUIDE.md` for detailed documentation
- Review terminal logs for error messages
- Check browser console for frontend errors

Happy quoting! 🚀
