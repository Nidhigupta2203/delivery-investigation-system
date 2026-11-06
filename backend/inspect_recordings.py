import sys
from app.core.database import SessionLocal
from app.models.delivery import Delivery
from app.models.recording import Recording
from sqlalchemy import select

def main():
    db = SessionLocal()
    delivery = db.scalar(select(Delivery).where(Delivery.delivery_number == 'DEL-01'))
    if not delivery:
        print('Delivery DEL-01 not found')
        return
    print('Delivery id:', delivery.id)
    recordings = db.scalars(select(Recording).where(Recording.delivery_id == delivery.id)).all()
    for r in recordings:
        print(f"Recording: {r.file_name} path={r.file_path} size={r.file_size_bytes} checksum={r.checksum_sha256}")

if __name__ == '__main__':
    main()
