import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.repository import *
from app.core.database import engine, Base

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done!")

# List tables
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Created tables: {', '.join(tables)}")
