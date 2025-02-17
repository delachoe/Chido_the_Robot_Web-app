import bcrypt
import os
from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv

# Load environment variables with explicit path
load_dotenv(r'C:\Users\taps\Documents\projects\res web app\.env')  # Update path!

# Load environment variables
host = os.getenv('MYSQL_HOST')
user = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
database = os.getenv('MYSQL_DB')

print(f"Host: {host}")
print(f"User: {user}")
print(f"DB: {database}")

# Verify loading
print("Loaded environment variables:")
print(f"Host: {os.getenv('MYSQL_HOST')}")
print(f"User: {os.getenv('MYSQL_USER')}")
print(f"DB: {os.getenv('MYSQL_DB')}")
# Create and configure Flask app

app = Flask(__name__)
app.config.update({
    'MYSQL_HOST': '127.0.0.1',  # Use IP instead of 'localhost'
    'MYSQL_USER': os.getenv('MYSQL_USER'),
    'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
    'MYSQL_DB': os.getenv('MYSQL_DB'),
    'MYSQL_PORT': 3306,  # Explicitly set port
    'MYSQL_CONNECT_TIMEOUT': 10
})


# Initialize MySQL
mysql = MySQL(app)

def create_admin():
    try:
        # Verify connection first
        with app.app_context():
            app.config['MYSQL_CONNECT_TIMEOUT'] = 10 
            conn = mysql.connection
            if not conn:
                raise Exception("No database connection")
                
            cur = conn.cursor()
            print("Successfully connected to database!")
            
            # Create admin user
            username = "admin"
            password = "admin123"  # Change if needed
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            cur.execute("""
                INSERT INTO users (username, password)
                VALUES (%s, %s)
            """, (username, hashed_pw))
            
            conn.commit()
            cur.close()
            print("Admin user created successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")
        if 'cur' in locals():
            cur.close()

if __name__ == '__main__':
    # Push app context explicitly
    with app.app_context():
        create_admin()