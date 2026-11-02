import os, sys
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.recording import Recording

def main():
    with SessionLocal() as db:
        rec = db.query(Recording).first()
        if rec:
            print('Recording ID:', rec.id)
            print('File path:', rec.file_path)
            print('Checksum:', rec.checksum_sha256)
        else:
            print('No recordings found')

if __name__ == '__main__':
    main()
