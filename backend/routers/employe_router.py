# backend/routers/employe_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db, User, FicheDePaie, HistoriqueEnvoi
from backend.services.auth import get_current_user

router = APIRouter(prefix="/api/employe", tags=["Employé"])


@router.get("/profil")
def profil(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "nom": user.nom, "prenom": user.prenom,
        "email": user.email, "poste": user.poste, "role": user.role
    }


@router.get("/fiches")
def mes_fiches(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fiches = db.query(FicheDePaie).filter(
        FicheDePaie.employe_id == user.id
    ).order_by(FicheDePaie.mois.desc()).all()
    return [
        {
            "id": f.id,
            "mois": f.mois,
            "salaire_net": f.salaire_net,
            "salaire_brut": f.salaire_brut,
            "cotisations": f.cotisations,
            "prime": f.prime,
            "heures": f.heures,
            "envoye": f.envoye,
            "envoye_le": f.envoye_le.strftime("%d/%m/%Y %H:%M") if f.envoye_le else None,
            "has_pdf": bool(f.pdf_path)
        }
        for f in fiches
    ]


@router.get("/fiches/{fiche_id}/pdf")
def telecharger_ma_fiche(fiche_id: int,
                          user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    fiche = db.query(FicheDePaie).filter(
        FicheDePaie.id == fiche_id,
        FicheDePaie.employe_id == user.id   # sécurité : l'employé ne voit QUE ses fiches
    ).first()
    if not fiche:
        raise HTTPException(404, "Fiche introuvable")
    if not fiche.pdf_path:
        raise HTTPException(404, "PDF non encore généré")
    return FileResponse(fiche.pdf_path, media_type="application/pdf",
                        filename=f"fiche_{fiche.mois}.pdf")


@router.get("/historique")
def mon_historique(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(HistoriqueEnvoi).filter(
        HistoriqueEnvoi.employe_id == user.id
    ).order_by(HistoriqueEnvoi.date_envoi.desc()).all()
    result = []
    for log in logs:
        fiche = db.query(FicheDePaie).filter(FicheDePaie.id == log.fiche_id).first()
        result.append({
            "mois": fiche.mois if fiche else "—",
            "date_envoi": log.date_envoi.strftime("%d/%m/%Y %H:%M"),
            "statut": log.statut,
        })
    return result
