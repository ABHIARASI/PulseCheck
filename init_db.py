from database import engine, Base
from models import MonitorResult, Monitor
Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")