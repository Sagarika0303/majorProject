import pymysql
import os

connection = pymysql.connect(
    host=os.environ['DB_HOST'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME'],
    port=int(os.environ.get('DB_PORT', 25524))
)
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM job_postings")
count = cursor.fetchone()[0]
print(f"Number of job postings: {count}")

cursor.close()
connection.close()
