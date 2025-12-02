import random
import string
from sqlalchemy.orm import Session
from app.models import Project


def generate_invite_code(db: Session) -> str:
    """
    Generate a unique 6-character invite code (uppercase letters + digits).
    Ensures the code doesn't already exist in the database.
    """
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Check if code already exists
        existing = db.query(Project).filter(Project.invite_code == code).first()
        if not existing:
            return code
