if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
        try {
            await navigator.serviceWorker.register("/sw.js?v=3");
            console.log("Service Worker registrado");
        } catch (error) {
            console.error("Error registrando Service Worker:", error);
        }
    });
}