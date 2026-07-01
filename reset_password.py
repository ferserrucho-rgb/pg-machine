"""
Password Reset Utility for PG Machine
Resets password for a user by email
"""
import sys
import bcrypt
import psycopg2
from psycopg2 import extras

def hash_password(plain: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def reset_password(database_url: str, email: str, new_password: str):
    """
    Reset password for a user.

    Args:
        database_url: PostgreSQL connection string
        email: User email
        new_password: New password (plain text, will be hashed)
    """
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # Check if user exists
        cur.execute("SELECT id, email, full_name FROM profiles WHERE email = %s", (email.lower().strip(),))
        user = cur.fetchone()

        if not user:
            print(f"❌ Error: User with email '{email}' not found")
            return False

        print(f"✓ Found user: {user['full_name']} ({user['email']})")
        print(f"  User ID: {user['id']}")

        # Hash new password
        password_hash = hash_password(new_password)

        # Update password
        cur.execute(
            "UPDATE profiles SET password_hash = %s WHERE id = %s",
            (password_hash, user['id'])
        )
        conn.commit()

        print(f"✅ Password updated successfully for {user['email']}")
        print(f"   New password: {new_password}")
        return True

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    # Database URL from Streamlit secrets or environment
    try:
        # Try to import streamlit and get from secrets
        import streamlit as st
        database_url = st.secrets["DATABASE_URL"]
        print("Using database URL from Streamlit secrets")
    except:
        # Fallback to environment variable or manual input
        import os
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("❌ Error: DATABASE_URL not found")
            print("Please set DATABASE_URL environment variable or run within Streamlit context")
            sys.exit(1)

    # User to reset
    email = "ferserrucho@gmail.com"
    new_password = "PGMachine2024!"  # Change this to desired password

    print("=" * 60)
    print("PG Machine - Password Reset Utility")
    print("=" * 60)
    print(f"Target user: {email}")
    print(f"New password: {new_password}")
    print("-" * 60)

    # Confirm
    response = input("Proceed with password reset? (yes/no): ").lower().strip()
    if response != "yes":
        print("Cancelled.")
        sys.exit(0)

    # Execute reset
    success = reset_password(database_url, email, new_password)

    print("=" * 60)
    if success:
        print("Password reset complete!")
        print(f"User can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {new_password}")
    else:
        print("Password reset failed.")
    print("=" * 60)
