(function () {
    "use strict";

    function onReady(fn) {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", fn);
        } else {
            fn();
        }
    }

    function clearResults(input, results) {
        results.hidden = true;
        results.innerHTML = "";
        input.setAttribute("aria-expanded", "false");
    }

    function renderResults(input, results, contactos) {
        results.innerHTML = "";
        if (!contactos.length) {
            clearResults(input, results);
            return;
        }

        contactos.forEach(function (contacto) {
            var button = document.createElement("button");
            var title = document.createElement("span");
            var meta = document.createElement("span");

            button.type = "button";
            button.className = "email-autocomplete-option";
            button.setAttribute("role", "option");

            title.className = "email-autocomplete-title";
            title.textContent = contacto.nombre + " — " + contacto.email;

            meta.className = "email-autocomplete-meta";
            meta.textContent = contacto.origen || "contacto";

            button.appendChild(title);
            button.appendChild(meta);
            button.addEventListener("click", function () {
                input.value = contacto.email;
                clearResults(input, results);
                input.focus();
            });
            results.appendChild(button);
        });

        results.hidden = false;
        input.setAttribute("aria-expanded", "true");
    }

    onReady(function () {
        var widget = document.querySelector("[data-email-autocomplete]");
        if (!widget) {
            return;
        }

        var input = widget.querySelector("[data-email-autocomplete-input]");
        var results = widget.querySelector("[data-email-autocomplete-results]");
        var timer = null;
        var controller = null;

        if (!input || !results) {
            return;
        }

        input.addEventListener("input", function () {
            var query = input.value.trim();
            window.clearTimeout(timer);
            if (controller) {
                controller.abort();
            }

            if (query.length < 2 || query.indexOf("@") !== -1) {
                clearResults(input, results);
                return;
            }

            timer = window.setTimeout(function () {
                controller = new AbortController();
                fetch("/emails/contactos?q=" + encodeURIComponent(query), {
                    headers: { "Accept": "application/json" },
                    signal: controller.signal,
                })
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error("contact_search_failed");
                        }
                        return response.json();
                    })
                    .then(function (contactos) {
                        renderResults(input, results, Array.isArray(contactos) ? contactos : []);
                    })
                    .catch(function (error) {
                        if (error.name !== "AbortError") {
                            clearResults(input, results);
                        }
                    });
            }, 220);
        });

        input.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                clearResults(input, results);
            }
        });

        document.addEventListener("click", function (event) {
            if (!widget.contains(event.target)) {
                clearResults(input, results);
            }
        });
    });
})();
