import sys, os
sys.path.append('backend')
from app.core.database import SessionLocal
with SessionLocal() as db:
    result = db.execute('SELECT id, file_path, checksum_sha256 FROM recordings LIMIT 1').first()
    print('Result:', result)
