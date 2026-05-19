(function (window) {
    "use strict";

    var proposalTemplates = {
        danos_agua: {
            tipo_trabajo: "Informe pericial por daños de agua",
            alcance: "Inspección técnica del inmueble.\nIdentificación de daños y zonas afectadas.\nAnálisis de posibles causas: fugas, filtraciones, condensaciones u otros aportes de humedad.\nReportaje fotográfico.\nRedacción de informe pericial con conclusiones técnicas.",
            plazo_estimado: "5-7 días desde la visita",
            condiciones: "El informe se entrega en formato digital PDF.\nNo incluye ensayos destructivos, catas ni pruebas de laboratorio.\nLa ratificación judicial solo se incluye si figura expresamente como línea de honorarios.\nVisitas adicionales o actuaciones complementarias se presupuestarán aparte."
        },
        humedades: {
            tipo_trabajo: "Informe pericial de humedades",
            alcance: "Inspección visual del inmueble.\nIdentificación de tipología de humedad: capilaridad, filtración, condensación u otras.\nAnálisis de daños observados y posibles causas.\nReportaje fotográfico.\nRedacción de informe técnico-pericial con diagnóstico y conclusiones.",
            plazo_estimado: "5-7 días desde la visita",
            condiciones: "El informe se entrega en formato digital PDF.\nNo incluye catas, ensayos destructivos ni mediciones especializadas no disponibles durante la visita.\nLa ratificación judicial solo se incluye si figura expresamente como línea de honorarios.\nActuaciones adicionales se presupuestarán aparte."
        },
        informe_judicial: {
            tipo_trabajo: "Informe pericial para procedimiento judicial",
            alcance: "Análisis técnico de la documentación facilitada.\nInspección del inmueble, si resulta necesaria.\nIdentificación y valoración técnica de los daños o patologías objeto del encargo.\nRedacción de informe pericial estructurado para su aportación al procedimiento.",
            plazo_estimado: "7-10 días desde la visita y recepción de la documentación necesaria",
            condiciones: "El informe se entrega en formato digital PDF.\nLa ratificación judicial solo se incluye si figura expresamente como línea de honorarios.\nReuniones adicionales, contrainformes o ampliaciones se presupuestarán aparte.\nLa documentación necesaria deberá ser aportada por el cliente antes de iniciar la redacción."
        },
        informe_aseguradora: {
            tipo_trabajo: "Informe pericial para reclamación ante aseguradora",
            alcance: "Inspección técnica de los daños comunicados.\nAnálisis del origen probable y alcance de los daños.\nReportaje fotográfico.\nRedacción de informe pericial orientado a reclamación frente a compañía aseguradora.",
            plazo_estimado: "5-7 días desde la visita",
            condiciones: "El informe se entrega en formato digital PDF.\nNo incluye gestiones directas con la compañía aseguradora, salvo pacto expreso.\nNo incluye ensayos destructivos ni actuaciones de reparación.\nLa ratificación judicial solo se incluye si figura expresamente como línea de honorarios."
        },
        inspeccion_previa: {
            tipo_trabajo: "Visita técnica de inspección previa",
            alcance: "Visita técnica al inmueble.\nInspección visual de las zonas indicadas por el cliente.\nToma de datos básicos y fotografías.\nOrientación técnica inicial sobre las actuaciones recomendables.",
            plazo_estimado: "Según disponibilidad de agenda",
            condiciones: "La visita no incluye informe pericial completo salvo contratación posterior.\nLas conclusiones iniciales tendrán carácter orientativo.\nLa ratificación judicial solo se incluye si figura expresamente como línea de honorarios.\nEn caso de contratar posteriormente el informe, podrá descontarse total o parcialmente el importe de la visita si así se acuerda."
        },
        tasacion_inmobiliaria: {
            tipo_trabajo: "Tasación inmobiliaria",
            alcance: "Inspección visual del inmueble.\nAnálisis de características físicas, funcionales y urbanísticas disponibles.\nRevisión de documentación aportada.\nAnálisis de mercado y testigos comparables cuando proceda.\nEstimación de valor y redacción de informe de valoración.",
            plazo_estimado: "5-7 días desde la visita y recepción de la documentación necesaria",
            condiciones: "La valoración se emitirá conforme a la documentación disponible y a la inspección realizada.\nNo constituye tasación hipotecaria homologada ECO salvo contratación expresa.\nNo incluye levantamiento topográfico, comprobaciones registrales exhaustivas, certificados administrativos ni gestiones ante terceros.\nCualquier ampliación por nueva documentación o cambio de alcance se presupuestará aparte."
        },
        inspeccion_vivienda: {
            tipo_trabajo: "Inspección técnica de vivienda",
            alcance: "Inspección visual general de la vivienda.\nRevisión del estado aparente de acabados, instalaciones visibles y elementos constructivos accesibles.\nIdentificación de incidencias observables.\nReportaje fotográfico básico.\nRedacción de resumen técnico o informe de observaciones.",
            plazo_estimado: "3-5 días desde la visita",
            condiciones: "La inspección se limita a elementos visibles y accesibles en el momento de la visita.\nNo incluye ensayos destructivos, comprobaciones ocultas, certificados oficiales, proyecto, dirección de obra ni valoración económica salvo contratación expresa.\nLas actuaciones adicionales se presupuestarán aparte."
        }
    };

    var lineCategoryTemplates = {
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

    function fillEmptyFields(form, template, fieldNames) {
        fieldNames.forEach(function (name) {
            var field = form.elements[name];
            if (field && field.value.trim() === "") {
                field.value = template[name] || "";
            }
        });
    }

    window.SistemaPericialPropuestasTemplates = {
        proposalTemplates: proposalTemplates,
        lineCategoryTemplates: lineCategoryTemplates,
        fillEmptyFields: fillEmptyFields
    };
}(window));
