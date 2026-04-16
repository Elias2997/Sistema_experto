const RULES = [
  {
    enfermedad: "Diabetes mellitus tipo 2",
    tipo: "metabolica",
    triggers: ["sed excesiva", "vision borrosa", "fatiga", "mareos"],
    objectHints: ["glucometro", "jeringa"],
    pruebas: [
      "glucosa en ayunas",
      "hemoglobina glicosilada",
      "perfil lipidico",
    ],
    tratamiento: [
      "control nutricional",
      "actividad fisica supervisada",
      "valoracion medica para manejo farmacologico",
    ],
    diagnostico:
      "Sospecha clinica compatible con diabetes mellitus tipo 2.",
  },
  {
    enfermedad: "Infeccion respiratoria aguda",
    tipo: "respiratoria",
    triggers: ["fiebre", "tos persistente", "dificultad respiratoria", "fatiga"],
    objectHints: [],
    pruebas: [
      "evaluacion clinica presencial",
      "oximetria de pulso",
      "radiografia de torax si hay alarma",
    ],
    tratamiento: [
      "hidratacion",
      "control de fiebre",
      "valoracion medica si la respiracion empeora",
    ],
    diagnostico:
      "El cuadro es compatible con una infeccion respiratoria que requiere vigilancia clinica.",
  },
  {
    enfermedad: "Gastroenteritis o sindrome digestivo agudo",
    tipo: "digestiva",
    triggers: ["dolor abdominal", "nauseas", "vomitos", "fiebre"],
    objectHints: [],
    pruebas: [
      "valoracion clinica",
      "electrolitos si hay deshidratacion",
      "estudios de heces si el cuadro persiste",
    ],
    tratamiento: [
      "hidratacion oral",
      "dieta blanda",
      "valoracion medica si hay dolor intenso o deshidratacion",
    ],
    diagnostico:
      "Sospecha de trastorno digestivo agudo con necesidad de seguimiento segun la evolucion.",
  },
  {
    enfermedad: "Cefalea o sindrome neurologico funcional",
    tipo: "neurologica",
    triggers: ["dolor de cabeza", "mareos", "vision borrosa", "vomitos"],
    objectHints: [],
    pruebas: [
      "exploracion neurologica",
      "control de signos vitales",
      "neuroimagen si existen signos de alarma",
    ],
    tratamiento: [
      "reposo",
      "hidratacion",
      "valoracion medica si el dolor es severo o progresivo",
    ],
    diagnostico:
      "Los hallazgos orientan a un sindrome neurologico inespecifico que requiere correlacion clinica.",
  },
  {
    enfermedad: "Sindrome coronario o dolor toracico de origen cardiovascular",
    tipo: "cardiovascular",
    triggers: ["dolor de pecho", "dificultad respiratoria", "mareos", "fatiga"],
    objectHints: [],
    pruebas: [
      "electrocardiograma",
      "troponinas",
      "valoracion urgente en un centro medico",
    ],
    tratamiento: [
      "evaluacion inmediata",
      "monitorizacion",
      "manejo hospitalario si el cuadro lo confirma",
    ],
    diagnostico:
      "Dolor toracico con necesidad de descartar una causa cardiovascular de forma prioritaria.",
  },
  {
    enfermedad: "Sindrome infeccioso general",
    tipo: "infecciosa",
    triggers: ["fiebre", "fatiga", "nauseas", "vomitos"],
    objectHints: ["pastillas"],
    pruebas: [
      "hemograma",
      "proteina C reactiva",
      "valoracion clinica segun foco sospechado",
    ],
    tratamiento: [
      "hidratacion",
      "reposo",
      "seguimiento medico para definir tratamiento especifico",
    ],
    diagnostico:
      "El cuadro sugiere un proceso infeccioso inespecifico que necesita correlacion clinica.",
  },
];

function uniqueStrings(values) {
  return [...new Set(values.filter(Boolean))];
}

function scoreRule(rule, input) {
  let score = 0;

  for (const symptom of input.sintomas) {
    if (rule.triggers.includes(symptom)) {
      score += 2;
    }
  }

  if (input.tipoEnfermedad === rule.tipo) {
    score += 3;
  }

  for (const hint of input.objetosDetectados) {
    if (rule.objectHints.includes(hint)) {
      score += 1;
    }
  }

  return score;
}

function chooseRule(input) {
  const ranked = RULES.map((rule) => ({
    rule,
    score: scoreRule(rule, input),
  })).sort((left, right) => right.score - left.score);

  const winner = ranked[0];

  if (winner && winner.score > 0) {
    return winner.rule;
  }

  return {
    enfermedad: "Sindrome clinico inespecifico",
    tipo: input.tipoEnfermedad,
    pruebas: [
      "valoracion clinica general",
      "signos vitales",
      "pruebas complementarias segun evolucion",
    ],
    tratamiento: [
      "observacion",
      "manejo sintomatico",
      "consulta medica si aparecen signos de alarma",
    ],
    diagnostico:
      "No hay suficientes hallazgos para una sospecha unica; se sugiere valoracion clinica general.",
  };
}

export function generateRuleBasedDiagnosis(input, reason = null) {
  const selectedRule = chooseRule(input);
  const sintomas = uniqueStrings([...input.sintomas, ...(selectedRule.triggers ?? [])])
    .slice(0, 6);
  const objetos = input.objetosDetectados.length
    ? ` Los objetos detectados (${input.objetosDetectados.join(", ")}) se usaron como apoyo contextual.`
    : "";
  const fallbackReason = reason ? ` Se activo el modo local porque ${reason}.` : "";

  return {
    diagnosis: {
      enfermedad: selectedRule.enfermedad,
      tipo: selectedRule.tipo,
      sintomas,
      pruebas: selectedRule.pruebas,
      diagnostico: selectedRule.diagnostico,
      tratamiento: selectedRule.tratamiento,
      explicacion:
        `La orientacion se genero con reglas clinicas basadas en los sintomas reportados y el tipo de enfermedad seleccionado.${objetos}${fallbackReason}`,
    },
    attempts: 0,
    model: "reglas-locales",
    usage: null,
    fallback: true,
  };
}
