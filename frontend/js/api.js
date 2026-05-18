// frontend/js/api.js — helpers partagés

const API = window.location.hostname === "localhost"
  ? "http://localhost:8000/api"
  : window.location.origin + "/api";

function getToken() { return localStorage.getItem("token"); }
function getUser()  { return JSON.parse(localStorage.getItem("user") || "{}"); }

function logout() {
  localStorage.clear();
  window.location.href = "/";
}

// Requête API avec token
async function apiFetch(path, options = {}) {
  const token = getToken();
  const res = await fetch(API + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erreur serveur");
  return data;
}

// Toast notification
function toast(msg, type = "success") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.style.background = type === "success" ? "#10B981"
                       : type === "error"   ? "#EF4444" : "#F59E0B";
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 3500);
}

// Initiales pour avatar
function initiales(nom, prenom) {
  return ((prenom || "")[0] + (nom || "")[0]).toUpperCase();
}

// Format montant MAD
function mad(val) {
  return Number(val).toLocaleString("fr-MA", { minimumFractionDigits: 2 }) + " MAD";
}

// Téléchargement PDF avec token JWT
async function telechargerPDF(ficheId, role) {
  try {
    const endpoint = role === "employeur"
      ? `/employeur/fiches/${ficheId}/pdf`
      : `/employe/fiches/${ficheId}/pdf`;

    const res = await fetch(API + endpoint, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });

    if (!res.ok) {
      const err = await res.json();
      return toast(err.detail || "Erreur téléchargement", "error");
    }

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `bulletin_${ficheId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    toast("Erreur lors du téléchargement", "error");
  }
}

// Sidebar mobile
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}
function closeSidebar() {
  document.querySelector('.sidebar').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
}
