"""Initialize database tables"""
from app.db.session import engine
from app.db.base import Base
from app.models.user import User
from app.models.invoice import Invoice

def init_database():
    """Create all database tables"""
    print("🗄️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Created tables: {', '.join(tables)}")

if __name__ == "__main__":
    init_database()
