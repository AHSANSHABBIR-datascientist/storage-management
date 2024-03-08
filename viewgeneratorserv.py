from Database.db_connector import connect_to_database
from flask import jsonify

class ViewGeneratorService:
    @staticmethod
    def generate_view(user_id):
        """Generates view for the user"""
        conn = connect_to_database()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM files WHERE user_id = %s
            """, (user_id,))
            files = cursor.fetchall()
            # Process files data as needed
            return jsonify({"files": files}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            conn.close()
