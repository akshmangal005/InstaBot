import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DB_URL')

def create_db():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        # SQL query to create a table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS SESSION (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(256),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        # Execute the query
        cursor.execute(create_table_query)
        conn.commit()  # Save changes

        print("Table 'SESSION' created successfully.")
        
        # Close connection
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

def post_sessionid(id):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Insert query
        insert_query = '''
            INSERT INTO SESSION (session_id) VALUES (%s) RETURNING id;
        '''

        # Execute the query
        cursor.execute(insert_query, (id,))
        
        # Fetch the generated ID (optional)
        session_id = cursor.fetchone()[0]
        print("Inserted Session ID:", session_id)

        # Commit and close
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error:", e)

def get_sessionid():
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Query to get the latest session_id
        latest_session_query = """
            SELECT session_id FROM SESSION 
            ORDER BY created_at DESC 
            LIMIT 1;
        """

        cursor.execute(latest_session_query)
        latest_session = cursor.fetchone()

        # Close connection
        cursor.close()
        conn.close()

        if latest_session:
            return latest_session[0]
        else:
            return None        

    except Exception as e:
        print("Error:", e)