from bot.db.database import engine
from sqlalchemy import text

def check_schemas():
    with engine.connect() as conn:
        result = conn.execute(text('SELECT schema_name FROM information_schema.schemata'))
        schemas = [row[0] for row in result]
        print('Schemas:', schemas)
        
        # Check if public schema exists and what tables it contains
        if 'public' in schemas:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print('Tables in public schema:', tables)
        
        # Check if any users table exists in any schema
        result = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'users'"))
        user_tables = [(row[0], row[1]) for row in result]
        print('Users tables found:', user_tables)

if __name__ == "__main__":
    check_schemas()