# main.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Charge les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optionnel, les vars peuvent etre definies manuellement

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, SessionLocal, User
from backend.services.auth import hash_password
from backend.routers import auth_router, employeur_router, employe_router

app = FastAPI(title="PaySlip Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(employeur_router.router)
app.include_router(employe_router.router)

# ── Fichiers statiques (frontend) ────────────────────────
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/dashboard-employeur")
def dashboard_emp():
    return FileResponse("frontend/pages/dashboard_employeur.html")

@app.get("/dashboard-employe")
def dashboard_employe():
    return FileResponse("frontend/pages/dashboard_employe.html")


# ── Init DB + seed ───────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()
    _seed()


def _seed():
    """Crée un compte employeur et 2 employés de démo si la DB est vide."""
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        employeur = User(
            email="employeur@demo.com",
            nom="Martin", prenom="Sophie",
            poste="DRH", role="employeur",
            hashed_password=hash_password("demo1234")
        )
        db.add(employeur)

        employes_demo = [
            ("Kofi", "Asante",   "kofi@demo.com",   "Développeur Backend"),
            ("Amina", "Diallo",  "amina@demo.com",  "Designer UX"),
        ]
        for prenom, nom, email, poste in employes_demo:
            db.add(User(
                email=email, nom=nom, prenom=prenom,
                poste=poste, role="employe",
                hashed_password=hash_password("demo1234")
            ))

        db.commit()
        print("✅ Comptes de démo créés")
    finally:
        db.close()
