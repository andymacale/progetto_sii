try {
    window.parent.localStorage.removeItem('auth_token');
    console.log("[Medical App] Token eliminato dal browser!");
} catch (e) {
    console.error("Errore eliminazione token:", e);
}