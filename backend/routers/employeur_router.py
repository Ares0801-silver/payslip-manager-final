# backend/routers/employeur_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.database import get_db, User, FicheDePaie, HistoriqueEnvoi
from backend.services.auth import require_employeur, hash_password
from backend.services.pdf_service import generer_fiche_pdf
from backend.services.email_service import envoyer_fiche_par_email

router = APIRouter(prefix="/api/employeur", tags=["Employeur"])


# ── Schémas ──────────────────────────────────────────────

class EmployeCreate(BaseModel):
    email: str
    nom: str
    prenom: str
    poste: str = ""
    password: str

class EmployeUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    poste: Optional[str] = None
    actif: Optional[bool] = None

class FicheCreate(BaseModel):
    employe_id: int
    mois: str            # "2026-04"
    salaire_brut: float
    cotisations: float
    prime: float = 0.0
    heures: float = 151.67

    @property
    def salaire_net(self):
        return self.salaire_brut + self.prime - self.cotisations


# ── Employés ─────────────────────────────────────────────

@router.get("/employes")
def liste_employes(db: Session = Depends(get_db), _=Depends(require_employeur)):
    employes = db.query(User).filter(User.role == "employe").all()
    return [
        {
            "id": e.id, "nom": e.nom, "prenom": e.prenom,
            "email": e.email, "poste": e.poste, "actif": e.actif,
            "created_at": e.created_at.strftime("%d/%m/%Y")
        }
        for e in employes
    ]


@router.post("/employes")
def ajouter_employe(data: EmployeCreate, db: Session = Depends(get_db), _=Depends(require_employeur)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email déjà utilisé")
    employe = User(
        email=data.email, nom=data.nom, prenom=data.prenom,
        poste=data.poste, role="employe",
        hashed_password=hash_password(data.password)
    )
    db.add(employe)
    db.commit()
    db.refresh(employe)
    return {"message": "Employé ajouté", "id": employe.id}


@router.patch("/employes/{employe_id}")
def modifier_employe(employe_id: int, data: EmployeUpdate,
                     db: Session = Depends(get_db), _=Depends(require_employeur)):
    emp = db.query(User).filter(User.id == employe_id, User.role == "employe").first()
    if not emp:
        raise HTTPException(404, "Employé introuvable")
    if data.nom is not None:    emp.nom = data.nom
    if data.prenom is not None: emp.prenom = data.prenom
    if data.poste is not None:  emp.poste = data.poste
    if data.actif is not None:  emp.actif = data.actif
    db.commit()
    return {"message": "Employé mis à jour"}


@router.delete("/employes/{employe_id}")
def retirer_employe(employe_id: int, db: Session = Depends(get_db), _=Depends(require_employeur)):
    emp = db.query(User).filter(User.id == employe_id, User.role == "employe").first()
    if not emp:
        raise HTTPException(404, "Employé introuvable")
    emp.actif = False   # désactivation douce
    db.commit()
    return {"message": "Employé désactivé"}


# ── Fiches de paie ───────────────────────────────────────

@router.get("/fiches")
def liste_fiches(db: Session = Depends(get_db), _=Depends(require_employeur)):
    fiches = db.query(FicheDePaie).all()
    result = []
    for f in fiches:
        emp = db.query(User).filter(User.id == f.employe_id).first()
        result.append({
            "id": f.id,
            "mois": f.mois,
            "employe_id": f.employe_id,
            "employe_nom": f"{emp.prenom} {emp.nom}" if emp else "—",
            "salaire_brut": f.salaire_brut,
            "salaire_net": f.salaire_net,
            "cotisations": f.cotisations,
            "prime": f.prime,
            "envoye": f.envoye,
            "envoye_le": f.envoye_le.strftime("%d/%m/%Y %H:%M") if f.envoye_le else None,
        })
    return result


@router.post("/fiches")
def creer_fiche(data: FicheCreate, db: Session = Depends(get_db), _=Depends(require_employeur)):
    emp = db.query(User).filter(User.id == data.employe_id, User.role == "employe").first()
    if not emp:
        raise HTTPException(404, "Employé introuvable")

    net = data.salaire_brut + data.prime - data.cotisations
    fiche = FicheDePaie(
        employe_id=data.employe_id,
        mois=data.mois,
        salaire_brut=data.salaire_brut,
        salaire_net=net,
        cotisations=data.cotisations,
        prime=data.prime,
        heures=data.heures
    )
    db.add(fiche)
    db.commit()
    db.refresh(fiche)

    # Génération PDF immédiate
    try:
        pdf_path = generer_fiche_pdf(fiche, emp)
        fiche.pdf_path = pdf_path
        db.commit()
    except Exception as e:
        pass  # PDF généré à l'envoi si échec ici

    return {"message": "Fiche créée", "id": fiche.id}


@router.post("/fiches/{fiche_id}/envoyer")
def envoyer_fiche(fiche_id: int, db: Session = Depends(get_db),
                  employeur: User = Depends(require_employeur)):
    fiche = db.query(FicheDePaie).filter(FicheDePaie.id == fiche_id).first()
    if not fiche:
        raise HTTPException(404, "Fiche introuvable")

    emp = db.query(User).filter(User.id == fiche.employe_id).first()

    # 1. Générer/regénérer le PDF
    pdf_path = generer_fiche_pdf(fiche, emp)
    fiche.pdf_path = pdf_path
    db.commit()

    # 2. Envoyer par email
    result = envoyer_fiche_par_email(
        employe_email=emp.email,
        employe_prenom=emp.prenom,
        employe_nom=emp.nom,
        mois=fiche.mois,
        pdf_path=pdf_path
    )

    statut  = "success" if result["success"] else "error"
    message = f"Fiche {fiche.mois} envoyée à {emp.email}" if result["success"]               else result.get("error", "Erreur inconnue")

    # 3. Mettre à jour la fiche si succès
    if result["success"]:
        fiche.envoye    = True
        fiche.envoye_le = datetime.utcnow()
        db.commit()

    # 4. Log historique (succès ou échec)
    log = HistoriqueEnvoi(
        fiche_id=fiche.id,
        employe_id=emp.id,
        envoye_par=employeur.id,
        statut=statut,
        message=message
    )
    db.add(log)
    db.commit()

    if not result["success"]:
        raise HTTPException(500, f"PDF généré mais email non envoyé : {result.get('error')}")

    return {"message": f"📧 Fiche envoyée par email à {emp.email}", "pdf": pdf_path}


@router.get("/fiches/{fiche_id}/pdf")
def telecharger_pdf(fiche_id: int, db: Session = Depends(get_db), _=Depends(require_employeur)):
    fiche = db.query(FicheDePaie).filter(FicheDePaie.id == fiche_id).first()
    if not fiche or not fiche.pdf_path:
        raise HTTPException(404, "PDF non disponible")
    return FileResponse(fiche.pdf_path, media_type="application/pdf",
                        filename=f"fiche_{fiche.mois}.pdf")


@router.get("/historique")
def historique(db: Session = Depends(get_db), _=Depends(require_employeur)):
    logs = db.query(HistoriqueEnvoi).order_by(HistoriqueEnvoi.date_envoi.desc()).all()
    result = []
    for log in logs:
        emp = db.query(User).filter(User.id == log.employe_id).first()
        fiche = db.query(FicheDePaie).filter(FicheDePaie.id == log.fiche_id).first()
        result.append({
            "id": log.id,
            "employe": f"{emp.prenom} {emp.nom}" if emp else "—",
            "mois": fiche.mois if fiche else "—",
            "date_envoi": log.date_envoi.strftime("%d/%m/%Y %H:%M"),
            "statut": log.statut,
            "message": log.message,
        })
    return result


@router.get("/stats")
def stats(db: Session = Depends(get_db), _=Depends(require_employeur)):
    total_employes = db.query(User).filter(User.role == "employe", User.actif == True).count()
    total_fiches   = db.query(FicheDePaie).count()
    fiches_envoyees = db.query(FicheDePaie).filter(FicheDePaie.envoye == True).count()
    fiches_en_attente = total_fiches - fiches_envoyees
    return {
        "total_employes": total_employes,
        "total_fiches": total_fiches,
        "fiches_envoyees": fiches_envoyees,
        "fiches_en_attente": fiches_en_attente,
    }
