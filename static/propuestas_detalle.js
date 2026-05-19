(function () {
    "use strict";

    function onReady(fn) {
        if (document.readyState !== "loading") {
            fn();
            return;
        }
        document.addEventListener("DOMContentLoaded", fn);
    }

    function setText(element, value) {
        if (element) {
            element.textContent = value || "";
        }
    }

    function readJsonElement(id) {
        var element = document.getElementById(id);
        if (!element) {
            return {};
        }

        try {
            return JSON.parse(element.textContent || "{}");
        } catch (error) {
            return {};
        }
    }

    function setupLineTemplateForm() {
        var sharedTemplates = window.SistemaPericialPropuestasTemplates || {};
        var templates = sharedTemplates.lineCategoryTemplates || {};
        var fillEmptyFields = sharedTemplates.fillEmptyFields;
        var form = document.querySelector("[data-line-template-form]");
        if (!form) {
            return;
        }

        var category = form.elements.categoria_servicio;
        var applyButton = form.querySelector("[data-apply-line-template]");
        if (!category || !applyButton) {
            return;
        }

        function applyTemplate() {
            var template = templates[category.value];
            if (template && fillEmptyFields) {
                fillEmptyFields(
                    form,
                    template,
                    ["concepto", "descripcion", "incluye", "no_incluye", "condiciones"]
                );
            }
        }

        applyButton.addEventListener("click", applyTemplate);
        category.addEventListener("change", applyTemplate);
    }

    function setupCatalogPreview() {
        var templates = readJsonElement("catalogo-servicios-preview-data");
        var form = document.querySelector("[data-catalog-service-form]");
        if (!form) {
            return;
        }

        var select = form.querySelector("[data-catalog-service-select]");
        var preview = form.querySelector("[data-catalog-service-preview]");
        var price = form.querySelector("[data-catalog-price]");
        var priceHelp = form.querySelector("[data-catalog-price-help]");
        if (!select || !preview) {
            return;
        }

        function renderPreview() {
            var template = templates[select.value];
            if (!template) {
                preview.hidden = true;
                return;
            }

            setText(form.querySelector("[data-catalog-preview-concepto]"), template.concepto);
            setText(form.querySelector("[data-catalog-preview-categoria]"), template.categoria);
            setText(form.querySelector("[data-catalog-preview-descripcion]"), template.descripcion);
            setText(form.querySelector("[data-catalog-preview-incluye]"), template.incluye);
            setText(form.querySelector("[data-catalog-preview-no-incluye]"), template.no_incluye);
            setText(form.querySelector("[data-catalog-preview-condiciones]"), template.condiciones);
            preview.hidden = false;
        }

        function updatePriceHelp() {
            if (!price || !priceHelp) {
                return;
            }

            var value = parseFloat(String(price.value || "").replace(",", "."));
            if (!Number.isFinite(value) || value <= 0) {
                priceHelp.textContent = "Introduce el importe antes de añadir. El servidor rechazará importes 0 o negativos.";
                priceHelp.className = "error";
                return;
            }

            priceHelp.textContent = "Importe listo para crear la línea del catálogo.";
            priceHelp.className = "subtitle";
        }

        select.addEventListener("change", renderPreview);
        if (price) {
            price.addEventListener("input", updatePriceHelp);
        }

        renderPreview();
        updatePriceHelp();
    }

    onReady(function () {
        setupLineTemplateForm();
        setupCatalogPreview();
    });
}());
