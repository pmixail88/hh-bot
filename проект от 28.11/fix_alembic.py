import os

alembic_ini_content = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql://neondb_owner:npg_X2MjE8RsNdDH@ep-solitary-brook-agmztrhf-pooler.c-2.eu-central-1.aws.neon.tech:5432/neondb?sslmode=require

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

# Удаляем старый файл если существует
if os.path.exists("alembic.ini"):
    os.remove("alembic.ini")

# Создаем новый файл с UTF-8 кодировкой
with open("alembic.ini", "w", encoding="utf-8") as f:
    f.write(alembic_ini_content)

print("✅ alembic.ini пересоздан с UTF-8 кодировкой")