# Streamlit Frontend

A modern, user-friendly web interface for the AI Invoice Automation system built with Streamlit.

## Features

### 🔐 Authentication
- User registration and login
- Secure token-based authentication
- Session management

### 📊 Dashboard
- Real-time statistics and metrics
- Invoice processing status
- Category distribution charts
- Recent invoices overview

### 📄 Invoice Management
- View all invoices with filtering
- Sort by category, status, date
- Detailed invoice information
- Pagination support

### 📤 Document Upload
- Drag-and-drop file upload
- Automatic document classification
- Real-time processing feedback
- Extract invoice data automatically

### 🔍 Semantic Search
- Natural language search queries
- Relevance-based results
- Quick document lookup

### 📈 Analytics
- Spending trends over time
- Category-wise analysis
- Top vendors
- Monthly reports

### 📧 Gmail Integration
- Connect Gmail account
- Auto-sync invoice emails
- Process email attachments
- Sync history tracking

## Installation

The required packages are already installed. If you need to install them manually:

```bash
pip install streamlit plotly pandas
```

## Running the Application

### Option 1: Complete Application (Backend + Frontend)

```bash
./run_app.sh
```

This will start:
- Backend API on http://localhost:8000
- Streamlit Frontend on http://localhost:8501

### Option 2: Frontend Only

If the backend is already running:

```bash
streamlit run streamlit_app.py
```

### Option 3: Custom Configuration

```bash
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## Stopping the Application

```bash
./stop_app.sh
```

Or manually:
```bash
# Stop backend
lsof -ti:8000 | xargs kill -9

# Stop frontend
lsof -ti:8501 | xargs kill -9
```

## Configuration

Edit `.streamlit/config.toml` to customize:
- Theme colors
- Server settings
- Browser behavior

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api/v1`

To change the API URL, edit the `API_BASE_URL` in `streamlit_app.py`:

```python
API_BASE_URL = "http://your-api-url:port/api/v1"
```

## Usage

1. **Start the application** using `./run_app.sh`

2. **Open your browser** to http://localhost:8501

3. **Register/Login** with your credentials

4. **Upload documents** via the Upload page

5. **View and manage** invoices on the Invoices page

6. **Search documents** using natural language queries

7. **Analyze spending** trends on the Analytics page

8. **Connect Gmail** for automatic invoice extraction

## Logs

View application logs:

```bash
# Backend logs
tail -f backend.log

# Frontend logs  
tail -f frontend.log
```

## Troubleshooting

### Frontend won't start
- Check if port 8501 is available: `lsof -i:8501`
- Stop any existing Streamlit processes: `pkill -f streamlit`

### Can't connect to backend
- Verify backend is running: `curl http://localhost:8000/`
- Check backend logs: `tail -f backend.log`
- Ensure API_BASE_URL is correct in streamlit_app.py

### Authentication issues
- Clear browser cache and cookies
- Check that the backend authentication endpoints are working
- Verify the API token is being stored correctly

## Features Overview

### Dashboard Widgets
- Total invoices count
- Processed vs pending status
- Total amount overview
- Category distribution pie chart
- Processing status bar chart
- Recent invoices table

### Invoice Filters
- Category filter
- Status filter
- Date range filter
- Pagination controls

### Search Capabilities
- Semantic search using AI embeddings
- Keyword-based filtering
- Multi-field search support

### File Upload Support
- PDF documents
- DOCX files
- CSV spreadsheets
- XLSX spreadsheets

## Technology Stack

- **Streamlit**: Web framework
- **Plotly**: Interactive charts
- **Pandas**: Data manipulation
- **Requests**: API communication

## Security

- Token-based authentication
- Secure password handling
- CORS protection
- XSRF protection enabled
