Steps 
Day - 1

git clone (github repo link)  --- It will open the github repo into VS code
git status -- for checking the project status 
git remote -v -- for origin 
mkdir frontend, backend, worker, docs 
mkdir backend/app
mkdir backend/app/api, backend/app/models, backend/app/schemas, backend/app/services
python --version
node --version
npm --version
git --version
npm install -g pnpm
pnpm --version
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
$env:Path = "C:\Users\nidhi\.local\bin;$env:Path"
uv --version
docker --version
docker compose version
<!-- git add backend/app/main.py docs/architecture.md docs/decisions.md
git commit -m "chore: add initial project structure and documentation"
git push origin main 
git status-->

Day - 2
docker info
{ wsl --install 
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --update
wsl --status
wsl -l -v } (in powersehll as administrator)
docker --version
docker compose version
docker run hello-world
cd backend
uv --version
uv init --name delivery-backend
uv add fastapi uvicorn sqlalchemy alembic "psycopg[binary]" pydantic-settings
Antigravity work 
git status
git ls-files | findstr /i ".env"
cd backend
delivery-investigation-system\backend>
uv --version
uv sync
uv run pytest -v
uv run uvicorn app.main:app --reload
http://127.0.0.1:8000/

Day - 3
for frontend -
cd frontend 
pnpm dev

for backend - 
cd backend 
uv run uvicorn app.main:app -- reload