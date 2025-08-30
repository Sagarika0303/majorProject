import pymysql

def fix_schema():
    connection = pymysql.connect(host='localhost', user='root', password='1533@sQl', db='cv')
    cursor = connection.cursor()
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN domain VARCHAR(100);")
    except Exception as e:
        print(f"Error adding domain column: {e}")
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN experience_level VARCHAR(50);")
    except Exception as e:
        print(f"Error adding experience_level column: {e}")
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN branch VARCHAR(100) DEFAULT 'Unknown';")
    except Exception as e:
        print(f"Error adding branch column: {e}")
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN phone_number VARCHAR(20);")
    except Exception as e:
        print(f"Error adding phone_number column: {e}")
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN missing_skills TEXT;")
    except Exception as e:
        print(f"Error adding missing_skills column: {e}")
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN resume_score INT;")
    except Exception as e:
        print(f"Error adding resume_score column: {e}")
    connection.commit()
    cursor.close()
    connection.close()
    print("Database schema fix completed.")

if __name__ == "__main__":
    fix_schema()
