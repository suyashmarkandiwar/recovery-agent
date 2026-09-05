import sys
import os
from datetime import date, timedelta
from sqlmodel import Session, select
from passlib.context import CryptContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import engine, create_db_and_tables
from app.db.models import Employee, Invoice

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    create_db_and_tables()
    
    with Session(engine) as session:
        if not session.exec(select(Employee)).first():
            admin = Employee(username="admin", hashed_password=pwd_context.hash("password123"))
            session.add(admin)
            
        if not session.exec(select(Invoice)).first():
            today = date.today()
            invoices = [
                Invoice(client_name="Gary", client_email="gadak99840@fidhost.com", client_phone = "+91 9874568321", amount=500.0, due_date=today - timedelta(days=5)),
                Invoice(client_name="Akash", client_email="beta@example.com", client_phone = "+91 9534568321", amount=1200.0, due_date=today - timedelta(days=15)),
                Invoice(client_name="Ash", client_email="wodarex357@liondapt.com", client_phone = "+91 9874129321", amount=3400.0, due_date=today - timedelta(days=25)),
                Invoice(client_name="Mukesh", client_email="delta@example.com", client_phone = "+91 9876548321", amount=8900.0, due_date=today - timedelta(days=35))
            ]
            session.add_all(invoices)
            
        session.commit()
        print("Neon database seeded successfully!")

if __name__ == "__main__":
    seed()