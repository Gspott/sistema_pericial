(function () {
    function ready(fn) {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", fn);
        } else {
            fn();
        }
    }

    ready(function () {
        var drawer = document.getElementById("app-drawer");
        var toggle = document.querySelector(".drawer-toggle");
        var overlay = document.querySelector(".drawer-overlay");
        var drawerLinks = drawer ? drawer.querySelectorAll(".drawer-link") : [];
        var drawerClosers = drawer ? drawer.querySelectorAll('[data-drawer-close="main-nav"]') : [];
        var quickToggle = document.querySelector(".app-new-link");
        var quickDrawer = document.getElementById("global-quick-actions-drawer");
        var quickClosers = quickDrawer ? quickDrawer.querySelectorAll('[data-quick-drawer-close="quick-actions"], .quick-drawer-link') : [];

        function setOverlayOpen(isOpen) {
            if (overlay) {
                overlay.classList.toggle("open", isOpen);
            }
            document.body.classList.toggle("drawer-open", isOpen);
        }

        function isDrawerOpen() {
            return !!drawer && drawer.classList.contains("open");
        }

        function isQuickOpen() {
            return !!quickDrawer && quickDrawer.classList.contains("open");
        }

        function syncOverlay() {
            setOverlayOpen(isDrawerOpen() || isQuickOpen());
        }

        function setDrawerOpen(isOpen) {
            if (!drawer || !toggle) {
                return;
            }
            if (isOpen && quickDrawer) {
                setQuickOpen(false, false);
            }
            drawer.classList.toggle("open", isOpen);
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
            syncOverlay();
        }

        function setQuickOpen(isOpen, returnFocus) {
            if (!quickDrawer || !quickToggle) {
                return;
            }
            if (isOpen && drawer) {
                setDrawerOpen(false);
            }
            quickDrawer.classList.toggle("open", isOpen);
            quickDrawer.setAttribute("aria-hidden", isOpen ? "false" : "true");
            quickToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
            quickToggle.setAttribute("aria-label", isOpen ? "Cerrar acciones rápidas" : "Abrir acciones rápidas");
            syncOverlay();

            if (isOpen) {
                var firstAction = quickDrawer.querySelector("a");
                if (firstAction) {
                    firstAction.focus();
                }
            } else if (returnFocus) {
                quickToggle.focus();
            }
        }

        if (drawer && toggle && drawer.dataset.initialized !== "1") {
            drawer.dataset.initialized = "1";

            toggle.addEventListener("click", function () {
                setDrawerOpen(!drawer.classList.contains("open"));
            });

            drawerLinks.forEach(function (closer) {
                closer.addEventListener("click", function () {
                    setDrawerOpen(false);
                });
            });

            drawerClosers.forEach(function (closer) {
                closer.addEventListener("click", function () {
                    setDrawerOpen(false);
                });
            });
        }

        if (quickToggle && quickDrawer && quickDrawer.dataset.initialized !== "1") {
            quickDrawer.dataset.initialized = "1";

            quickToggle.addEventListener("click", function (event) {
                event.stopPropagation();
                setQuickOpen(!quickDrawer.classList.contains("open"), false);
            });

            quickClosers.forEach(function (closer) {
                closer.addEventListener("click", function () {
                    setQuickOpen(false, false);
                });
            });
        }

        if (overlay) {
            overlay.addEventListener("click", function () {
                setDrawerOpen(false);
                setQuickOpen(false, false);
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                if (isQuickOpen()) {
                    setQuickOpen(false, true);
                } else if (isDrawerOpen()) {
                    setDrawerOpen(false);
                }
            }
        });
    });
})();
