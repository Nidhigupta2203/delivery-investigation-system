'''#!/usr/bin/env python
'''
# Update the expected_checksum of a specific FileTransfer record.
# Usage: python update_expected_checksum.py <file_transfer_id> <new_checksum>

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from uuid import UUID

# Import the SQLAlchemy session and models
from app.core.database import SessionLocal
from app.models.transfer import FileTransfer

def main():
    if len(sys.argv) != 3:
        print("Usage: python update_expected_checksum.py <file_transfer_id> <new_checksum>")
        sys.exit(1)

    ft_id_str = sys.argv[1]
    new_checksum = sys.argv[2]

    try:
        ft_id = UUID(ft_id_str)
    except ValueError:
        print(f"Invalid UUID: {ft_id_str}")
        sys.exit(1)

    db = SessionLocal()
    try:
        ft = db.get(FileTransfer, ft_id)
        if not ft:
            print(f"FileTransfer with ID {ft_id} not found.")
            sys.exit(1)
        # Update expected_checksum
        ft.expected_checksum = new_checksum
        db.commit()
        print(f"Updated expected_checksum for FileTransfer {ft_id} to {new_checksum}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
