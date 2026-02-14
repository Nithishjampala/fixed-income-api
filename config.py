import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # MySQL Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "appuser")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "fixed_income_db")
    
    # SSL for Aiven
    SSL_CA_PATH = os.getenv("SSL_CA_PATH", "./ca.pem")
    USE_SSL = os.getenv("ENVIRONMENT") == "production"
    
    @property
    def DATABASE_URL(self):
        """Get database URL with SSL parameters for Aiven"""
        base_url = f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        
        if self.USE_SSL:
            return f"{base_url}?ssl_ca={self.SSL_CA_PATH}&ssl_verify_identity=true"
        else:
            return base_url

settings = Settings()
