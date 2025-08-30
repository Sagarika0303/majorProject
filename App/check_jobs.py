import pymysql

connection = pymysql.connect(host='localhost', user='root', password='1533@sQl', db='cv')
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM job_postings")
count = cursor.fetchone()[0]
print(f"Number of job postings: {count}")

cursor.close()
connection.close()
