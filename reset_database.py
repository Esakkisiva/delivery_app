#!/usr/bin/env python3
"""
Database Reset Script
This script will drop all existing tables and recreate them with the correct schema.
"""

import pymysql
from sqlalchemy import create_engine, text
from database import DATABASE_URL
from models.auth_models import User, OTP
from models.address_models import Address
from models.order_models import Order, OrderItem
from models.delivery_models import DeliveryAgent

def reset_database():
    """Drop all tables and recreate them with correct schema"""
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("🔧 Resetting database...")
            
            # Disable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
            
            # Drop all tables in correct order
            tables_to_drop = [
                "order_items",
                "orders", 
                "delivery_agents",
                "addresses",
                "otps",
                "users"
            ]
            
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    print(f"✅ Dropped table: {table}")
                except Exception as e:
                    print(f"⚠️  Could not drop {table}: {e}")
            
            # Re-enable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
            
            print("✅ All tables dropped successfully")
            
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False
    
    # Recreate tables
    try:
        print("🔨 Recreating tables...")
        
        # Import all models to ensure they're registered
        from models.auth_models import User, OTP
        from models.address_models import Address
        from models.order_models import Order, OrderItem
        from models.delivery_models import DeliveryAgent
        
        # Create tables
        from database import Base
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables recreated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error recreating tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database reset...")
    success = reset_database()
    
    if success:
        print("🎉 Database reset completed successfully!")
        print("📋 You can now test your endpoints.")
    else:
        print("💥 Database reset failed!")
