import os
import sys
import time

# Ensure backend/app is importable when worker runs as a standalone process
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.transfer_service import poll_and_process_pending_jobs, process_transfer_job

__all__ = ["poll_and_process_pending_jobs", "process_transfer_job"]


def main():
    """CLI loop for running the standalone transfer worker."""
    print("Starting Delivery Transfer Background Worker...")
    try:
        while True:
            processed = poll_and_process_pending_jobs()
            if processed > 0:
                print(f"Processed {processed} transfer job(s).")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Worker stopped by user.")


if __name__ == "__main__":
    main()
