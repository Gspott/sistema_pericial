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
        var closers = document.querySelectorAll("[data-drawer-close], .drawer-link");

        if (!drawer || !toggle) {
            return;
        }
        if (drawer.dataset.initialized === "1") {
            return;
        }
        drawer.dataset.initialized = "1";

        function setOpen(isOpen) {
            drawer.classList.toggle("open", isOpen);
            if (overlay) {
                overlay.classList.toggle("open", isOpen);
            }
            document.body.classList.toggle("drawer-open", isOpen);
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        }

        toggle.addEventListener("click", function () {
            setOpen(!drawer.classList.contains("open"));
        });

        closers.forEach(function (closer) {
            closer.addEventListener("click", function () {
                setOpen(false);
            });
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                setOpen(false);
            }
        });
    });
})();
