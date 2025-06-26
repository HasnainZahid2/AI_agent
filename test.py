import psycopg2

try:
    conn = psycopg2.connect(
        dbname="usage_data",
        user="postgres",
        password="12345678",
        host="localhost",
        port="5432"
    )
    print("✅ Database connection successful.")
    conn.close()
except Exception as e:
    print("❌ Database connection failed:", e)
