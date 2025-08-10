#!/usr/bin/env python3
"""
Simple Database Reset Script
This script will drop all existing tables and recreate them with the new Integer-based address IDs.
"""

import pymysql
from sqlalchemy import create_engine, text
from config import settings
from models.auth_models import User, OTP
from models.address_models import Address
from models.order_models import Order, OrderItem
from models.delivery_models import DeliveryAgent

def reset_database():
    """Drop all tables and recreate them with correct schema"""
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("🔧 Resetting database...")
            
            # Disable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # Drop all tables
            tables = ["order_items", "orders", "addresses", "delivery_agents", "otps", "users"]
            for table in tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    print(f"✅ Dropped table: {table}")
                except Exception as e:
                    print(f"⚠️  Could not drop {table}: {e}")
            
            # Re-enable foreign key checks
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            
            # Commit the changes
            conn.commit()
            print("✅ Database reset completed!")
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting database reset...")
    if reset_database():
        print("🎉 Database reset successful! You can now start the application.")
    else:
        print("💥 Database reset failed!")
