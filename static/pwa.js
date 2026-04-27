if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
        try {
            await navigator.serviceWorker.register("/sw.js?v=4");
            console.log("Service Worker registrado");
        } catch (error) {
            console.error("Error registrando Service Worker:", error);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const topNav = document.querySelector(".top-nav");
    if (!topNav) {
        return;
    }

    const mobileQuery = window.matchMedia("(max-width: 767px)");
    let lastScrollY = window.scrollY;

    const updateTopNavVisibility = () => {
        if (!mobileQuery.matches) {
            topNav.classList.remove("is-hidden");
            lastScrollY = window.scrollY;
            return;
        }

        const currentScrollY = window.scrollY;
        const scrollingDown = currentScrollY > lastScrollY;

        if (currentScrollY <= 80) {
            topNav.classList.remove("is-hidden");
        } else if (scrollingDown) {
            topNav.classList.add("is-hidden");
        }

        lastScrollY = currentScrollY;
    };

    updateTopNavVisibility();
    window.addEventListener("scroll", updateTopNavVisibility, { passive: true });
    window.addEventListener("resize", updateTopNavVisibility);
});
