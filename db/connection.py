import mysql.connector

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="your_password_here",   # put you MySQL root password 
            database="ams_db"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"DB Connection Error: {e}")
        return None
