try {
    // Usiamo __TOKEN__ come segnaposto che Python sostituirà
    window.parent.localStorage.setItem('auth_token', '__TOKEN__');
    console.log("[Medical App] Token salvato con successo nel browser!");
} catch (e) {
    console.error("[Medical App] Errore salvataggio LocalStorage:", e);
}