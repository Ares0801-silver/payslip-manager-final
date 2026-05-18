# backend/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./payslip.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Modèles ──────────────────────────────────────────────

class User(Base):
    """Employeur ou employé"""
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    email    = Column(String, unique=True, index=True, nullable=False)
    nom      = Column(String, nullable=False)
    prenom   = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role     = Column(String, default="employe")   # "employeur" | "employe"
    poste    = Column(String, nullable=True)
    actif    = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fiches   = relationship("FicheDePaie", back_populates="employe", foreign_keys="FicheDePaie.employe_id")


class FicheDePaie(Base):
    """Fiche de paie d'un employé pour un mois donné"""
    __tablename__ = "fiches_de_paie"

    id           = Column(Integer, primary_key=True, index=True)
    employe_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    mois         = Column(String, nullable=False)   # ex: "2026-04"
    salaire_brut = Column(Float, nullable=False)
    salaire_net  = Column(Float, nullable=False)
    cotisations  = Column(Float, nullable=False)
    prime        = Column(Float, default=0.0)
    heures       = Column(Float, default=151.67)
    pdf_path     = Column(String, nullable=True)
    envoye       = Column(Boolean, default=False)
    envoye_le    = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    employe      = relationship("User", back_populates="fiches", foreign_keys=[employe_id])


class HistoriqueEnvoi(Base):
    """Log de chaque envoi de fiche"""
    __tablename__ = "historique_envois"

    id         = Column(Integer, primary_key=True, index=True)
    fiche_id   = Column(Integer, ForeignKey("fiches_de_paie.id"))
    employe_id = Column(Integer, ForeignKey("users.id"))
    envoye_par = Column(Integer, ForeignKey("users.id"))   # id de l'employeur
    date_envoi = Column(DateTime, default=datetime.utcnow)
    statut     = Column(String, default="success")         # "success" | "error"
    message    = Column(String, nullable=True)


# ── Helpers ──────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
