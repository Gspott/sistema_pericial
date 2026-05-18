(function () {
    "use strict";

    var templates = {
        estudio_documental: {
            concepto: "Estudio preliminar y análisis documental",
            descripcion: "Revisión inicial de la documentación aportada y valoración técnica preliminar del encargo.",
            incluye: "Análisis documental inicial, identificación de información necesaria y valoración preliminar de viabilidad técnica.",
            no_incluye: "Visita técnica, informe definitivo, mediciones instrumentales, ensayos ni ratificación judicial.",
            condiciones: "El alcance queda condicionado a la documentación facilitada por el cliente."
        },
        visita_tecnica: {
            concepto: "Visita técnica",
            descripcion: "Inspección técnica del inmueble o elemento objeto de análisis.",
            incluye: "Desplazamiento dentro del ámbito pactado, inspección visual, toma de datos y reportaje fotográfico básico.",
            no_incluye: "Catas, ensayos de laboratorio, medios auxiliares especiales, drones, segundas visitas ni actuaciones no previstas.",
            condiciones: "La visita queda condicionada al acceso efectivo al inmueble y a la disponibilidad de la documentación necesaria."
        },
        informe_pericial: {
            concepto: "Redacción de informe pericial",
            descripcion: "Elaboración de informe pericial técnico conforme al objeto del encargo.",
            incluye: "Análisis técnico, redacción del informe, incorporación de fotografías/anexos disponibles y entrega en PDF.",
            no_incluye: "Ratificación judicial, ampliaciones por nueva documentación, modificaciones por estrategia procesal, traducciones ni copias impresas.",
            condiciones: "El informe se emitirá conforme a la documentación disponible y observaciones realizadas durante la inspección."
        },
        ratificacion_judicial: {
            concepto: "Ratificación judicial",
            descripcion: "Asistencia del perito para ratificación del informe pericial en sede judicial.",
            incluye: "Preparación previa y asistencia a una única vista o señalamiento.",
            no_incluye: "Suspensiones, nuevos señalamientos, ampliaciones, desplazamientos, dietas, reuniones adicionales ni nueva documentación no prevista.",
            condiciones: "Cualquier suspensión judicial, nueva vista o actuación adicional será presupuestada aparte."
        },
        desplazamientos: {
            concepto: "Desplazamiento",
            descripcion: "Desplazamiento asociado a la actuación técnica.",
            incluye: "Kilometraje o desplazamiento según lo indicado en la línea.",
            no_incluye: "Dietas, peajes, aparcamientos, pernoctaciones o desplazamientos adicionales salvo pacto expreso.",
            condiciones: "Los desplazamientos adicionales o fuera del ámbito previsto podrán presupuestarse aparte."
        },
        extras: {
            concepto: "Servicio adicional",
            descripcion: "Actuación adicional vinculada al encargo pericial.",
            incluye: "La actuación descrita expresamente en esta línea.",
            no_incluye: "Actuaciones no descritas, nuevas visitas, ampliaciones documentales o trabajos de alcance diferente.",
            condiciones: "Cualquier ampliación del alcance será presupuestada aparte."
        }
    };

    function onReady(fn) {
        if (document.readyState !== "loading") {
            fn();
            return;
        }
        document.addEventListener("DOMContentLoaded", fn);
    }

    function fillEmptyFields(form, template) {
        ["concepto", "descripcion", "incluye", "no_incluye", "condiciones"].forEach(function (name) {
            var field = form.elements[name];
            if (field && field.value.trim() === "") {
                field.value = template[name] || "";
            }
        });
    }

    onReady(function () {
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
            if (template) {
                fillEmptyFields(form, template);
            }
        }

        applyButton.addEventListener("click", applyTemplate);
        category.addEventListener("change", applyTemplate);
    });
}());
