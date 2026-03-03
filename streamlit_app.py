import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Optional

# Configure page
st.set_page_config(
    page_title="AI Invoice Automation",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


# API Helper Functions
def api_request(method: str, endpoint: str, data: Optional[dict] = None, files: Optional[dict] = None):
    """Make API request."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None


# Page: Dashboard
def dashboard_page():
    """Main dashboard page."""
    st.title("📊 Dashboard")
    
    # Get invoice stats
    stats_response = api_request("GET", "/invoices/stats")
    
    if stats_response and stats_response.get("success"):
        stats = stats_response.get("data", {})
        
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Invoices", stats.get("total_invoices", 0))
        with col2:
            st.metric("Processed", stats.get("processed_invoices", 0))
        with col3:
            st.metric("Pending", stats.get("pending_invoices", 0))
        with col4:
            st.metric("Total Amount", f"${stats.get('total_amount', 0):,.2f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Invoices by category
            category_data = stats.get("invoices_by_category", {})
            if category_data:
                fig = px.pie(
                    names=list(category_data.keys()),
                    values=list(category_data.values()),
                    title="Invoices by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Processing status
            status_data = {
                "Processed": stats.get("processed_invoices", 0),
                "Pending": stats.get("pending_invoices", 0)
            }
            fig = px.bar(
                x=list(status_data.keys()),
                y=list(status_data.values()),
                title="Processing Status",
                labels={"x": "Status", "y": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent invoices
        st.subheader("📄 Recent Invoices")
        recent = stats.get("recent_invoices", [])
        if recent:
            df = pd.DataFrame(recent)
            # Display relevant columns
            display_cols = ["invoice_number", "vendor_name", "total", "invoice_date", "status"]
            available_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
        else:
            st.info("No invoices yet. Upload some documents to get started!")


# Page: Invoices
def invoices_page():
    """Invoices management page."""
    st.title("📄 Invoices")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        category_filter = st.selectbox("Category", ["All", "invoice", "receipt", "purchase_order", "contract", "statement", "other"])
    with col2:
        status_filter = st.selectbox("Status", ["All", "pending", "processed", "failed"])
    with col3:
        limit = st.number_input("Items per page", min_value=10, max_value=100, value=50)
    with col4:
        st.write("")
        refresh = st.button("🔄 Refresh")
    
    # Build query parameters
    params = {"skip": 0, "limit": limit}
    if category_filter != "All":
        params["category"] = category_filter
    if status_filter != "All":
        params["status"] = status_filter
    
    # Get invoices
    response = api_request("GET", "/invoices/", data=params)
    
    if response and response.get("success"):
        data = response.get("data", [])
        total = response.get("total", 0)
        
        st.info(f"Total: {total} invoices")
        
        if data:
            df = pd.DataFrame(data)
            
            # Display table with formatting
            display_cols = []
            for col in ["id", "invoice_number", "vendor_name", "total", "invoice_date", "status", "category"]:
                if col in df.columns:
                    display_cols.append(col)
            
            st.dataframe(df[display_cols], use_container_width=True)
            
            # Invoice details expander
            st.subheader("Invoice Details")
            invoice_id = st.selectbox("Select Invoice ID", df["id"].tolist() if "id" in df.columns else [])
            
            if invoice_id:
                invoice = df[df["id"] == invoice_id].iloc[0].to_dict()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"Invoice Number: {invoice.get('invoice_number', 'N/A')}")
                    st.write(f"Vendor: {invoice.get('vendor_name', 'N/A')}")
                    st.write(f"Category: {invoice.get('category', 'N/A')}")
                    st.write(f"Status: {invoice.get('status', 'N/A')}")
                
                with col2:
                    st.write("**Financial Details**")
                    st.write(f"Amount: ${invoice.get('amount', 0):,.2f}")
                    st.write(f"Tax: ${invoice.get('tax', 0):,.2f}")
                    st.write(f"Total: ${invoice.get('total', 0):,.2f}")
                    st.write(f"Currency: {invoice.get('currency', 'USD')}")
        else:
            st.info("No invoices found.")


# Page: Upload Document
def upload_page():
    """Document upload page."""
    st.title("📤 Upload Document")
    
    st.markdown("""
    Upload invoices, receipts, or other documents for automatic processing and extraction.
    Supported formats: PDF, DOCX, CSV, XLSX
    """)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "csv", "xlsx"],
        help="Upload a document for processing"
    )
    
    if uploaded_file:
        st.success(f"File selected: {uploaded_file.name}")
        
        # Additional metadata
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", ["invoice", "receipt", "purchase_order", "contract", "statement", "other"])
        with col2:
            auto_classify = st.checkbox("Auto-classify document", value=True)
        
        if st.button("Upload & Process"):
            with st.spinner("Uploading and processing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"category": category}
                
                response = api_request("POST", "/documents/upload", data=data, files=files)
                
                if response and response.get("success"):
                    st.success("Document uploaded and processed successfully!")
                    result = response.get("data", {})
                    
                    # Display extracted data
                    st.subheader("Extracted Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Document Type:** {result.get('document_type', 'N/A')}")
                        st.write(f"**Category:** {result.get('category', 'N/A')}")
                        st.write(f"**Confidence:** {result.get('classification_confidence', 0)*100:.1f}%")
                    
                    with col2:
                        st.write(f"**File Size:** {result.get('file_size', 0)} bytes")
                        st.write(f"**Status:** {result.get('status', 'N/A')}")
                    
                    # Show extracted data if available
                    extracted = result.get("extracted_data")
                    if extracted:
                        st.json(extracted)
                else:
                    st.error("Failed to upload document")


# Page: Search
def search_page():
    """Semantic search page."""
    st.title("🔍 Search Documents")
    
    search_query = st.text_input("Enter search query", placeholder="e.g., invoices from Acme Corp")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.slider("Number of results", min_value=5, max_value=50, value=10)
    with col2:
        st.write("")
        search_button = st.button("Search")
    
    if search_button and search_query:
        with st.spinner("Searching..."):
            params = {"query": search_query, "limit": limit}
            response = api_request("GET", "/search/semantic", data=params)
            
            if response and response.get("success"):
                results = response.get("data", [])
                
                if results:
                    st.success(f"Found {len(results)} results")
                    
                    for i, result in enumerate(results, 1):
                        with st.expander(f"Result {i} - Score: {result.get('score', 0):.3f}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**File:** {result.get('file_name', 'N/A')}")
                                st.write(f"**Category:** {result.get('category', 'N/A')}")
                                st.write(f"**Vendor:** {result.get('vendor_name', 'N/A')}")
                            with col2:
                                st.write(f"**Amount:** ${result.get('total', 0):,.2f}")
                                st.write(f"**Date:** {result.get('invoice_date', 'N/A')}")
                                st.write(f"**Status:** {result.get('status', 'N/A')}")
                else:
                    st.info("No results found")


# Page: Analytics
def analytics_page():
    """Analytics page."""
    st.title("📈 Analytics")
    
    response = api_request("GET", "/analytics/")
    
    if response and response.get("success"):
        data = response.get("data", {})
        
        # Time period selector
        period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
        
        # Metrics by category
        st.subheader("Spending by Category")
        category_totals = data.get("category_totals", {})
        if category_totals:
            fig = px.bar(
                x=list(category_totals.keys()),
                y=list(category_totals.values()),
                labels={"x": "Category", "y": "Total Amount ($)"},
                title="Total Spending by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Vendor analysis
        st.subheader("Top Vendors")
        vendor_data = data.get("top_vendors", [])
        if vendor_data:
            df = pd.DataFrame(vendor_data)
            st.dataframe(df, use_container_width=True)
        
        # Monthly trend
        st.subheader("Monthly Trend")
        monthly_data = data.get("monthly_trend", {})
        if monthly_data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(monthly_data.keys()),
                y=list(monthly_data.values()),
                mode='lines+markers',
                name='Amount'
            ))
            fig.update_layout(
                title="Monthly Invoice Amounts",
                xaxis_title="Month",
                yaxis_title="Amount ($)"
            )
            st.plotly_chart(fig, use_container_width=True)


# Page: Gmail Integration
def gmail_page():
    """Gmail integration page with IMAP support."""
    st.title("📧 Gmail Integration")
    
    st.markdown("""
    Connect your Gmail account to automatically fetch and process invoice attachments.
    **Note:** For Gmail, you need to use an App Password. [Learn how to create one](https://support.google.com/accounts/answer/185833)
    """)
    
    # Check connection status
    status_response = api_request("GET", "/gmail/imap/status")
    is_connected = False
    connected_email = None
    
    if status_response and status_response.get("success"):
        is_connected = status_response.get("data", {}).get("connected", False)
        connected_email = status_response.get("data", {}).get("email")
    
    # Connection Section
    st.subheader("📮 Gmail Connection")
    
    if is_connected:
        st.success(f"✅ Connected to: {connected_email}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔌 Disconnect", type="secondary"):
                disconnect_response = api_request("POST", "/gmail/imap/disconnect")
                if disconnect_response and disconnect_response.get("success"):
                    st.success("Disconnected successfully!")
                    st.rerun()
        with col2:
            if st.button("🔄 Refresh Messages"):
                st.rerun()
    else:
        st.info("👇 Enter your Gmail credentials to connect")
        
        with st.form("gmail_connect_form"):
            email = st.text_input("📧 Gmail Address", placeholder="your.email@gmail.com")
            password = st.text_input("🔑 App Password", type="password", 
                                    help="Use Gmail App Password, not your regular password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("🔗 Connect", type="primary", use_container_width=True)
            with col2:
                st.markdown("[📖 How to get App Password](https://support.google.com/accounts/answer/185833)")
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    with st.spinner("Connecting to Gmail..."):
                        connect_response = api_request("POST", "/gmail/imap/connect", {
                            "email": email,
                            "password": password
                        })
                        
                        if connect_response and connect_response.get("success"):
                            st.success(f"✅ Connected to {email}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Connection failed. Please check your credentials and make sure you're using an App Password.")
    
    # Messages Section (only show if connected)
    if is_connected:
        st.markdown("---")
        st.subheader("📨 Email Messages")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            limit = st.slider("Number of messages", 10, 100, 50)
        with col2:
            if st.button("🔄 Fetch Messages", type="primary"):
                with st.spinner("Fetching messages..."):
                    messages_response = api_request("GET", "/gmail/imap/messages", {
                        "limit": limit,
                        "has_attachments": True
                    })
                    
                    if messages_response and messages_response.get("success"):
                        messages = messages_response.get("data", [])
                        st.session_state["gmail_messages"] = messages
                        st.success(f"✅ Fetched {len(messages)} messages with attachments")
        
        # Display messages
        if "gmail_messages" in st.session_state:
            messages = st.session_state["gmail_messages"]
            
            if messages:
                st.write(f"**{len(messages)} messages with attachments**")
                
                for idx, msg in enumerate(messages):
                    with st.expander(f"📧 {msg.get('subject', 'No Subject')} - {msg.get('from', 'Unknown')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**From:** {msg.get('from')}")
                            st.write(f"**Date:** {msg.get('date')}")
                        with col2:
                            st.write(f"**Subject:** {msg.get('subject')}")
                            st.write(f"**Attachments:** {len(msg.get('attachments', []))}")
                        
                        # Show attachments
                        attachments = msg.get('attachments', [])
                        if attachments:
                            st.write("**📎 Attachments:**")
                            for att in attachments:
                                size_kb = att.get('size', 0) / 1024
                                st.write(f"- {att.get('filename')} ({size_kb:.1f} KB)")
            else:
                st.info("No messages with attachments found")


# Main App
def main():
    """Main application."""
    
    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'Dashboard'
    
    # Top bar with Gmail quick access
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.markdown("")  # Spacer
    with col2:
        if st.button("📧 Gmail", use_container_width=True):
            st.session_state.page = "Gmail Integration"
            st.rerun()
    with col3:
        # Connection status indicator
        status_response = api_request("GET", "/gmail/imap/status")
        if status_response and status_response.get("success"):
            is_connected = status_response.get("data", {}).get("connected", False)
            if is_connected:
                st.success("🟢")
            else:
                st.info("⚪")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=Invoice+AI", use_column_width=True)
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["Dashboard", "Invoices", "Upload", "Search", "Analytics", "Gmail Integration"],
            index=["Dashboard", "Invoices", "Upload", "Search", "Analytics", "Gmail Integration"].index(st.session_state.page)
        )
        
        # Update session state when sidebar selection changes
        if page != st.session_state.page:
            st.session_state.page = page
    
    # Use the page from session state
    current_page = st.session_state.page
    
    # Main content
    if current_page == "Dashboard":
        dashboard_page()
    elif current_page == "Invoices":
        invoices_page()
    elif current_page == "Upload":
        upload_page()
    elif current_page == "Search":
        search_page()
    elif current_page == "Analytics":
        analytics_page()
    elif current_page == "Gmail Integration":
        gmail_page()


if __name__ == "__main__":
    main()
