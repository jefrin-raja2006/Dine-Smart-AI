from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app.database.connection import SessionLocal
from app.models.models import User
from app.security import hash_password

email = input("Admin email: ").strip().lower()
name = input("Admin name: ").strip()
password = getpass("Choose admin password: ")
confirm = getpass("Confirm admin password: ")

if not email or not name:
    raise SystemExit("Email and name are required.")

if password != confirm:
    raise SystemExit("Passwords do not match.")

if len(password) < 12:
    raise SystemExit("Use a password with at least 12 characters.")

db = SessionLocal()

try:
    existing = db.query(User).filter(User.email == email).first()

    if existing:
        print(f"An account already exists for {email}. No changes made.")
    else:
        admin = User(
            name=name,
            email=email,
            password=hash_password(password),
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Admin account created. ID: {admin.id}, email: {admin.email}, role: {admin.role}")

except IntegrityError:
    db.rollback()
    print("Could not create the account. Check the database schema and constraints.")

finally:
    db.close()
