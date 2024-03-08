# storagemgmtserv.py
from Database.db_connector import connect_to_database
from flask import jsonify

class StorageMgmtServ:
    @staticmethod
    def allocate_initial_storage(user_id):
        """Allocates initial storage for a new user."""
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO storage (user_id, storage_used)
                VALUES (%s, %s)
            """, (user_id, 0))  # Allocate 0 bytes initially
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def save_file_info(user_id, filename, filesize, filepath):
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO files (user_id, filename, filesize, upload_date)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, filename, filesize))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_storage_usage(user_id, file_size_change):
        """Updates the storage used by a user. `file_size_change` can be positive (new file) or negative (file deleted)."""
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT storage_used FROM storage WHERE user_id = %s
            """, (user_id,))
            storage_used = cursor.fetchone()[0]

            new_storage_used = storage_used + file_size_change
            if new_storage_used > (10 * 1024 * 1024):  # Check if new usage exceeds the limit
                return False, "Storage limit exceeded."

            cursor.execute("""
                UPDATE storage SET storage_used = %s WHERE user_id = %s
            """, (new_storage_used, user_id))
            conn.commit()

            if new_storage_used >= (10 * 1024 * 1024) * 0.8:  # Alert if new usage exceeds 80%
                print("User nearing storage limit.")  # Replace with actual notification logic

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
        return True, "Storage updated successfully."

    @staticmethod
    def check_storage_limit(user_id, file_size):
        current_usage = StorageMgmtServ.get_storage_usage(user_id)
        if current_usage + file_size > 10 * 1024 * 1024:  # 10MB limit
            return False
        return True

    @staticmethod
    def get_storage_usage(user_id):
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT storage_used FROM storage WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                storage_used = result[0]
                return storage_used
            return 0
        finally:
            cursor.close()
            conn.close()
