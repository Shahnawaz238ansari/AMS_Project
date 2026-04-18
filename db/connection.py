import mysql.connector

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="MD@785892",   # apna MySQL password yahan
            database="ams_db"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"DB Connection Error: {e}")
        return None