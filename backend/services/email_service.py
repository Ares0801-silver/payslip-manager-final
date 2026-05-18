# backend/services/email_service.py
import os
import resend

# Ta clé API Resend — à mettre dans le .env
resend.api_key = os.getenv("RESEND_API_KEY", "")

# L'adresse expéditeur (doit correspondre à un domaine vérifié sur Resend)
# En mode test, tu peux utiliser : onboarding@resend.dev
FROM_ADDRESS = os.getenv("FROM_ADDRESS", "onboarding@resend.dev")
FROM_NAME    = os.getenv("FROM_NAME", "PaySlip Manager")


def envoyer_fiche_par_email(employe_email: str, employe_prenom: str,
                             employe_nom: str, mois: str,
                             pdf_path: str) -> dict:
    if not resend.api_key:
        return {"success": False, "error": "Clé API Resend manquante (RESEND_API_KEY)"}

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        corps_html = f"""
        <div style="font-family:'Segoe UI',sans-serif;max-width:600px;margin:auto;color:#1A2D42;">
          <div style="background:#0F1F3D;padding:28px 32px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:#00A8E8;margin:0;font-size:24px;">💼 PaySlip Manager</h1>
            <p style="color:rgba(255,255,255,0.6);margin:8px 0 0;font-size:14px;">Votre bulletin de paie est disponible</p>
          </div>
          <div style="background:#ffffff;padding:32px;border:1px solid #E5EDF2;">
            <p style="font-size:16px;">Bonjour <strong>{employe_prenom} {employe_nom}</strong>,</p>
            <p style="margin:18px 0;line-height:1.6;">Veuillez trouver ci-joint votre bulletin de paie pour la période <strong style="color:#0F1F3D;">{mois}</strong>.</p>
            <div style="background:#E8F4FD;border-left:4px solid #00A8E8;padding:16px 20px;border-radius:0 8px 8px 0;margin:24px 0;">
              📎 <strong>Le PDF est joint à cet email.</strong><br>
              <span style="color:#8FA3B1;font-size:13px;">Ce document est strictement confidentiel et vous est destiné personnellement.</span>
            </div>
            <p style="line-height:1.6;">Pour toute question, rapprochez-vous de votre service RH.</p>
            <p style="margin-top:28px;color:#8FA3B1;font-size:13px;border-top:1px solid #E5EDF2;padding-top:20px;">
              Cordialement,<br><strong style="color:#0F1F3D;">Le Service RH</strong><br><em>via PaySlip Manager</em>
            </p>
          </div>
          <div style="background:#F0F4F8;padding:14px;border-radius:0 0 12px 12px;text-align:center;font-size:11px;color:#8FA3B1;">
            Document généré automatiquement — Ne pas répondre à cet email
          </div>
        </div>
        """

        params = {
            "from": f"{FROM_NAME} <{FROM_ADDRESS}>",
            "to": [employe_email],
            "subject": f"Votre bulletin de paie — {mois}",
            "html": corps_html,
            "attachments": [
                {
                    "filename": f"bulletin_{mois}.pdf",
                    "content": list(pdf_bytes),
                }
            ],
        }

        response = resend.Emails.send(params)

        if response and response.get("id"):
            return {"success": True, "email_id": response["id"]}
        else:
            return {"success": False, "error": "Resend n'a pas retourné d'ID — vérifie ta clé API"}

    except FileNotFoundError:
        return {"success": False, "error": "PDF introuvable — générez d'abord la fiche"}
    except Exception as e:
        return {"success": False, "error": str(e)}
