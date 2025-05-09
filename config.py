from config import DB_CONFIG  # ✅ Add this line at the top

def run_query(query, params=None):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:
                return cursor.fetchall()
            conn.commit()
