
from Database.db_connector import connect_to_database
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify, session
from storagemgmtserv import StorageMgmtServ

class IdentityAccessManagementService:
    @staticmethod
    def signup(username, email, password):
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            hashed_password = password

            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, (username, email, hashed_password))
            conn.commit()
            user_id = cursor.lastrowid  # Fetch the newly created user ID
            StorageMgmtServ.allocate_initial_storage(user_id)  # Initialize storage for the new user
        except Exception as e:
            conn.rollback()
            raise e  # Enhanced error handling is recommended
        finally:
            cursor.close()
            conn.close()

    # @staticmethod
    # def signin(username, password):
    #     conn = connect_to_database()
    #     cursor = conn.cursor(dictionary=True)
    #     try:
    #         cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    #         user = cursor.fetchone()
    #         if user and user['password_hash'] == password:
    #             return user['id'], True  # Return user ID and authentication status
    #         else:
    #             return None, False
    #     except Exception as e:
    #         return None, False
    #     finally:
    #         cursor.close()
    #         conn.close()
    @staticmethod
    def signin(username, password):
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and user['password_hash'] == password:
                return user['id'], True  # Adjusted to return user ID and authentication status
            else:
                return None, False
        except Exception as e:
            return None, False
        finally:
            cursor.close()
            conn.close()
