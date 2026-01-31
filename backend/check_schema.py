"""
Check table schema - view column details
"""
from db_config import get_connection

def check_table_schema(table_name='candidates'):
    """Display all columns in a table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # PostgreSQL query to get column info
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        print(f"\n📋 SCHEMA FOR TABLE: {table_name}")
        print("=" * 80)
        for col in columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  • {col[0]:25} {col[1]:20} {nullable:10} {default}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    check_table_schema('candidates')
