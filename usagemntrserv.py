# usagemntrserv.py
from Database.db_connector import connect_to_database

class UsageMonitorService:
    @staticmethod
    def track_usage(user_id, data_volume):
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO usage_log (user_id, action, data_used, timestamp)
                VALUES (%s, 'File Upload', %s, NOW())
            """, (user_id, data_volume))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def check_daily_bandwidth(user_id):
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT SUM(data_used) FROM usage_log
                WHERE user_id = %s AND DATE(timestamp) = CURDATE()
            """, (user_id,))
            daily_usage = cursor.fetchone()[0] or 0
            if daily_usage > (25 * 1024 * 1024):  # 25MB limit
                return False
            return True
        except Exception as e:
            raise e
        finally:
            cursor.close()
            conn.close()
