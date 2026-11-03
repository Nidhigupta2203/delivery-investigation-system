import sys, os
sys.path.append(os.path.abspath('backend'))
from app.core.database import SessionLocal
with SessionLocal() as db:
    rec = db.execute('SELECT id, file_path, checksum_sha256 FROM recordings LIMIT 1').first()
    print('Recording entry:', rec)
