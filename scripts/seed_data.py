#!/usr/bin/env python3
"""
Script to seed initial data for testing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger()


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def seed_users():
    """Seed test users."""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_user = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_user:
            logger.info("Users already exist, skipping seed")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            gmail_connected=False
        )
        
        # Create test user
        test_user = User(
            email="test@example.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            gmail_connected=False
        )
        
        db.add(admin_user)
        db.add(test_user)
        db.commit()
        
        logger.info("Seeded users:")
        logger.info("  - admin@example.com (password: admin123)")
        logger.info("  - test@example.com (password: test123)")
        
    except Exception as e:
        logger.error(f"Error seeding users: {str(e)}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function to run all seed operations."""
    logger.info("Starting database seed...")
    
    create_tables()
    seed_users()
    
    logger.info("Database seed completed!")


if __name__ == "__main__":
    main()
