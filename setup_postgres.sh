#!/bin/bash

# PostgreSQL Setup Script for AI Invoice Automation

echo "🗄️  PostgreSQL Database Setup"
echo "================================"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed."
    echo ""
    echo "Install PostgreSQL:"
    echo "  macOS:   brew install postgresql@15"
    echo "  Ubuntu:  sudo apt-get install postgresql postgresql-contrib"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL is installed"
echo ""

# Database configuration
DB_NAME="invoice_automation_db"
DB_USER="invoice_user"
DB_PASSWORD="invoice_pass_2026"
DB_HOST="localhost"
DB_PORT="5432"

echo "📝 Database Configuration:"
echo "   Database: $DB_NAME"
echo "   User:     $DB_USER"
echo "   Host:     $DB_HOST"
echo "   Port:     $DB_PORT"
echo ""

# Start PostgreSQL service
echo "🚀 Starting PostgreSQL service..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew services start postgresql@15 2>/dev/null || brew services start postgresql 2>/dev/null
    sleep 2
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo service postgresql start
    sleep 2
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL may not be running. Attempting to start..."
    pg_ctl -D /usr/local/var/postgres start 2>/dev/null || \
    pg_ctl -D /opt/homebrew/var/postgres start 2>/dev/null
    sleep 3
fi

echo "✅ PostgreSQL service is running"
echo ""

# Create database user
echo "👤 Creating database user..."
psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || \
psql -d postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || \
createuser -U postgres $DB_USER 2>/dev/null || \
echo "   User may already exist"

# Grant privileges
psql -U postgres -c "ALTER USER $DB_USER CREATEDB;" 2>/dev/null || \
psql -d postgres -c "ALTER USER $DB_USER CREATEDB;" 2>/dev/null

# Create database
echo "🗄️  Creating database..."
psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || \
psql -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || \
createdb -U postgres -O $DB_USER $DB_NAME 2>/dev/null || \
echo "   Database may already exist"

# Grant all privileges
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || \
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null

echo "✅ Database created"
echo ""

# Update .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating .env file..."
    cat > "$ENV_FILE" << EOF
# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

# Application
APP_NAME=AI Invoice & Attachment Automation
DEBUG=False

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI (Optional - add your key)
OPENAI_API_KEY=

# Pinecone (Optional - add your key)
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=invoice-embeddings

# Gmail API (Optional)
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
EOF
    echo "✅ .env file created"
else
    # Update existing .env file
    if grep -q "^DATABASE_URL=" "$ENV_FILE"; then
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME|" "$ENV_FILE"
        echo "✅ Updated DATABASE_URL in .env"
    else
        echo "" >> "$ENV_FILE"
        echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" >> "$ENV_FILE"
        echo "✅ Added DATABASE_URL to .env"
    fi
fi

echo ""
echo "🎉 PostgreSQL setup complete!"
echo ""
echo "📊 Database Connection String:"
echo "   postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "🔧 Useful Commands:"
echo "   Connect to database:  psql -U $DB_USER -d $DB_NAME"
echo "   List databases:       psql -U postgres -l"
echo "   Drop database:        dropdb -U postgres $DB_NAME"
echo ""
echo "▶️  Next Steps:"
echo "   1. Make sure the app is stopped: ./stop_app.sh"
echo "   2. Run migrations (if using Alembic): alembic upgrade head"
echo "   3. Start the app: ./run_app.sh"
echo ""
