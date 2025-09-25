# QuoteSnap Backend

QuoteSnap is a Gmail quotation automation agent that processes emails and generates Excel quotations automatically.

## Database Setup

### Database Technology
- **Primary Database**: SQLite (lightweight, file-based)  
- **Location**: `backend/database/quotesnap.db`
- **Phase 2**: Vector database (Pinecone/Qdrant) for semantic search

### Database Schema
The application uses 4 main tables:
1. **emails** - Raw email data and metadata
2. **quotation_requests** - Extracted/structured quotation data  
3. **quotation_history** - Generated quotations and file paths
4. **logs** - System audit trail and events

### Local Setup Instructions

#### 1. Environment Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Environment Configuration
```bash
# Copy environment template
copy .env.example .env

# Edit .env file with your actual values:
# - Gmail API credentials
# - OpenAI API key
# - Other configuration settings
```

#### 3. Database Initialization

**Option A: Automatic (Recommended)**
```bash
# Run the application - database will be created automatically
python app.py
```

**Option B: Manual Initialization**
```bash
# Initialize database manually
python init_db.py init

# Check database status
python init_db.py status

# Reset database (if needed)
python init_db.py reset
```

#### 4. Database Management Commands

```bash
# Initialize database tables
python init_db.py init

# Check current database status
python init_db.py status

# Reset database (deletes all data)
python init_db.py reset
```

### Database Configuration

The database configuration is managed in `config/settings.py`:

```python
# Development
DATABASE_URL = 'sqlite:///database/quotesnap.db'

# Production (if using PostgreSQL later)
# DATABASE_URL = 'postgresql://user:password@localhost/quotesnap'
```

### Database Structure

#### emails table
```sql
CREATE TABLE emails (
    id TEXT PRIMARY KEY,
    gmail_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    sender TEXT,
    recipient TEXT,
    received_at DATETIME,
    body_text TEXT,
    body_html TEXT,
    attachments TEXT,  -- JSON array
    status TEXT DEFAULT 'received',
    processed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### quotation_requests table
```sql
CREATE TABLE quotation_requests (
    id TEXT PRIMARY KEY,
    email_id TEXT NOT NULL,
    client_name TEXT,
    client_email TEXT,
    client_phone TEXT,
    client_company TEXT,
    requirements TEXT,  -- JSON array
    deadline DATE,
    priority TEXT DEFAULT 'normal',
    estimated_value DECIMAL(10,2),
    status TEXT DEFAULT 'pending',
    extracted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails (id)
);
```

### Running the Application

#### Development Mode
```bash
# Start the Flask development server
python app.py

# Or use the run script
python run.py
```

#### Production Considerations
- Use environment variables for sensitive configuration
- Consider PostgreSQL for production deployment
- Set up proper logging and monitoring
- Use reverse proxy (nginx) in production

### Database Migration (Future)

For future schema changes, consider implementing:
- Database migration scripts
- Version tracking for schema changes
- Backup procedures before migrations

### Troubleshooting

#### Common Issues

**Database file not found:**
```bash
# Make sure the database directory exists
mkdir -p database

# Initialize the database
python init_db.py init
```

**Permission errors:**
```bash
# Check file permissions
ls -la database/

# Fix permissions if needed (Linux/Mac)
chmod 664 database/quotesnap.db
```

**Connection errors:**
- Check that SQLite is available in your Python environment
- Ensure the database directory is writable
- Verify the DATABASE_URL in your .env file

### Phase 2 Database Extensions

In Phase 2, we'll add:
- **Vector Database**: For semantic search of historical quotations
- **Embeddings Storage**: OpenAI embeddings for quotation matching
- **Supplier Database**: Contact information and communication history

Example Phase 2 additions:
```python
# Vector database configuration
VECTOR_DB_URL = "qdrant://localhost:6333"
EMBEDDING_MODEL = "text-embedding-ada-002"
```

## Quick Start

1. Clone the repository
2. Set up virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows)
4. Install deps: `pip install -r requirements.txt`
5. Copy config: `copy .env.example .env`
6. Edit `.env` with your API keys
7. Run: `python app.py`
8. Visit: http://localhost:5000

The database will be created automatically on first run!