from app import app, db, User
import bcrypt

def add_user(username, password):
    with app.app_context():
        try:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            new_user = User(username=username, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            print(f"User '{username}' added successfully!")
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    add_user("admin2", "admin122")