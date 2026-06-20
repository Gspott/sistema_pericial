(function () {
    "use strict";

    const DEFAULT_DEBOUNCE_MS = 1200;
    const DEFAULT_RETRY_MS = 1500;
    const STATES = {
        ready: "Listo para editar",
        dirty: "Cambios pendientes",
        saving: "Guardando...",
        saved: "Guardado",
        error: "Error al guardar",
        conflict: "Conflicto de guardado",
    };

    function parseDebounce(value) {
        const parsed = Number.parseInt(value || "", 10);
        if (Number.isNaN(parsed) || parsed < 300) {
            return DEFAULT_DEBOUNCE_MS;
        }
        return parsed;
    }

    function formatTime(value) {
        const date = value ? new Date(value) : new Date();
        if (Number.isNaN(date.getTime())) {
            return "";
        }
        return date.toLocaleTimeString("es-ES", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function setStatus(form, state, message, timestamp) {
        const statusSelector = form.dataset.autosaveStatus;
        const statusEl = statusSelector
            ? document.querySelector(statusSelector)
            : form.querySelector("[data-autosave-status-indicator]");
        if (!statusEl) {
            return;
        }
        const labelEl = statusEl.querySelector("[data-autosave-status-label]") || statusEl;
        const resolved = message || STATES[state] || STATES.ready;
        const time = state === "saved" ? formatTime(timestamp) : "";
        statusEl.dataset.autosaveState = state;
        statusEl.classList.remove("ready", "dirty", "saving", "saved", "error", "conflict");
        statusEl.classList.add(state);
        labelEl.textContent = time ? `${resolved} ${time}` : resolved;
    }

    function getUpdatedAtInput(form) {
        const selector = form.dataset.autosaveUpdatedAt;
        if (selector) {
            return document.querySelector(selector);
        }
        return form.querySelector('input[name="updated_at"]');
    }

    function updateKnownTimestamp(form, value) {
        if (!value) {
            return;
        }
        const updatedAtInput = getUpdatedAtInput(form);
        if (updatedAtInput) {
            updatedAtInput.value = value;
        }
    }

    function markDirty(controller) {
        if (controller.conflict) {
            return;
        }
        controller.dirty = true;
        setStatus(controller.form, "dirty");
        clearTimeout(controller.timer);
        controller.timer = window.setTimeout(() => {
            save(controller);
        }, controller.debounceMs);
    }

    function buildPayload(form) {
        const payload = new FormData(form);
        const updatedAtInput = getUpdatedAtInput(form);
        if (updatedAtInput && !payload.has("updated_at")) {
            payload.append("updated_at", updatedAtInput.value || "");
        }
        payload.append("autosave", "1");
        return payload;
    }

    async function postAutosave(controller) {
        const response = await fetch(controller.url, {
            method: "POST",
            body: buildPayload(controller.form),
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "autosave",
            },
        });
        let data = {};
        try {
            data = await response.json();
        } catch (error) {
            data = {};
        }
        if (!response.ok || data.ok === false) {
            const error = new Error(data.message || STATES.error);
            error.status = response.status;
            error.data = data;
            throw error;
        }
        return data;
    }

    async function save(controller, options) {
        const force = options && options.force;
        if (controller.saving || controller.conflict) {
            return;
        }
        if (!controller.dirty && !force) {
            return;
        }
        controller.saving = true;
        controller.dirty = false;
        setStatus(controller.form, "saving");
        try {
            const data = await postAutosave(controller);
            updateKnownTimestamp(controller.form, data.updated_at);
            setStatus(controller.form, "saved", data.message || STATES.saved, data.saved_at || data.updated_at);
            controller.retryCount = 0;
        } catch (error) {
            const data = error.data || {};
            if (data.conflict || error.status === 409) {
                controller.conflict = true;
                setStatus(controller.form, "conflict", data.message || "Otro proceso ha modificado el registro.");
            } else if (controller.retryCount < 1) {
                controller.retryCount += 1;
                controller.dirty = true;
                setStatus(controller.form, "error", "Error al guardar. Reintentando...");
                window.setTimeout(() => save(controller, { force: true }), DEFAULT_RETRY_MS);
            } else {
                controller.dirty = true;
                setStatus(controller.form, "error", data.message || STATES.error);
            }
        } finally {
            controller.saving = false;
        }
    }

    function attachAutosave(form) {
        if (form.dataset.autosaveBound === "1") {
            return;
        }
        const url = form.dataset.autosaveUrl;
        if (!url) {
            return;
        }
        const controller = {
            form,
            url,
            debounceMs: parseDebounce(form.dataset.autosaveDebounce),
            timer: null,
            dirty: false,
            saving: false,
            conflict: false,
            retryCount: 0,
        };
        form.dataset.autosaveBound = "1";
        setStatus(form, "ready");
        form.addEventListener("input", () => markDirty(controller));
        form.addEventListener("change", () => markDirty(controller));
        form.addEventListener("blur", () => {
            if (controller.dirty) {
                clearTimeout(controller.timer);
                save(controller);
            }
        }, true);
        form.addEventListener("submit", () => {
            clearTimeout(controller.timer);
        });
        window.addEventListener("beforeunload", (event) => {
            if (!controller.dirty && !controller.saving) {
                return;
            }
            event.preventDefault();
            event.returnValue = "";
        });
    }

    function initAutosave(root) {
        const scope = root || document;
        scope.querySelectorAll("[data-autosave-form]").forEach(attachAutosave);
    }

    window.SistemaPericialAutosave = {
        init: initAutosave,
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => initAutosave());
    } else {
        initAutosave();
    }
})();
