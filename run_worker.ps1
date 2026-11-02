# PowerShell wrapper to start the delivery transfer worker using the backend's uv environment
# This ensures the same virtual environment (with FastAPI, SQLAlchemy, Boto3, etc.)

# Change to the backend directory where the pyproject.toml lives
Set-Location "$PSScriptRoot\backend"

# Sync dependencies for the backend environment
uv sync

# Add the project root (one level up) to PYTHONPATH so the worker package can be discovered
$env:PYTHONPATH = "$PSScriptRoot\..;$env:PYTHONPATH"

# Run the worker module using the backend's environment
uv run python -m worker.transfer_worker