import asyncio
import aiomysql
import os
from dotenv import load_dotenv
import ssl

load_dotenv()

async def test_connection():
    host = os.getenv('MYSQL_HOST')
    port = int(os.getenv('MYSQL_PORT'))
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    
    print(f"🔌 Connecting to {host}:{port}...")
    
    # Create SSL context that doesn't verify certificate (for testing)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
    try:
        # Try with SSL context
        pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db='mysql',
            autocommit=True,
            ssl=ssl_ctx,
            charset='utf8mb4',
            program_name='fixed-income-api'
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT VERSION(), CURRENT_USER()")
                version, user = await cursor.fetchone()
                print(f"✅ CONNECTION SUCCESSFUL!")
                print(f"📊 MySQL Version: {version}")
                print(f"👤 Connected as: {user}")
                
                # List databases
                await cursor.execute("SHOW DATABASES")
                databases = await cursor.fetchall()
                print("📚 Available databases:")
                for db in databases:
                    print(f"   - {db[0]}")
        
        pool.close()
        await pool.wait_closed()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
