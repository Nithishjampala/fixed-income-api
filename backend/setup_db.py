import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_database():
    try:
        # Connection details
        host = os.getenv('MYSQL_HOST')
        port = int(os.getenv('MYSQL_PORT'))
        user = os.getenv('MYSQL_USER')
        password = os.getenv('MYSQL_PASSWORD')
        db_name = os.getenv('MYSQL_DATABASE', 'fixed_income_db')
        
        print(f"📡 Connecting to MySQL at {host}:{port}...")
        
        # First connect without database to create it
        pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db='defaultdb',  # Connect to default database first
            autocommit=True,
            ssl={'ca': '/etc/secrets/ca.pem'}
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Create database if it doesn't exist
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                print(f"✅ Database '{db_name}' created/verified")
                
                # Show databases
                await cursor.execute("SHOW DATABASES")
                dbs = await cursor.fetchall()
                print("📊 Available databases:")
                for db in dbs:
                    print(f"   - {db[0]}")
        
        pool.close()
        await pool.wait_closed()
        
        # Now connect to the actual database
        pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=db_name,
            autocommit=True,
            ssl={'ca': '/etc/secrets/ca.pem'}
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Create tables (simplified version)
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fixed_income_securities (
                        id VARCHAR(36) PRIMARY KEY,
                        security_name VARCHAR(255) NOT NULL,
                        security_type VARCHAR(50) NOT NULL,
                        face_value DECIMAL(15,2) NOT NULL,
                        coupon_rate DECIMAL(5,2),
                        coupon_frequency VARCHAR(20),
                        issue_date DATE,
                        maturity_date DATE,
                        day_count_convention VARCHAR(20),
                        currency VARCHAR(3) DEFAULT 'USD',
                        issuer VARCHAR(255),
                        credit_rating VARCHAR(20)
                    )
                """)
                print("✅ Table 'fixed_income_securities' created/verified")
                
                # Create portfolios table
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolios (
                        id VARCHAR(36) PRIMARY KEY,
                        portfolio_name VARCHAR(255) NOT NULL,
                        description TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                print("✅ Table 'portfolios' created/verified")
        
        pool.close()
        await pool.wait_closed()
        
        print("\n🎉 Database setup complete! Ready to run the API.")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(setup_database())
