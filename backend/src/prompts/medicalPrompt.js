const RESPONSE_EXAMPLE = {
  enfermedad: "Diabetes mellitus tipo 2",
  tipo: "metabolica",
  sintomas: ["sed excesiva", "poliuria", "fatiga"],
  pruebas: ["glucosa en ayunas", "hemoglobina glicosilada", "perfil lipidico"],
  diagnostico:
    "El cuadro clinico es compatible con una sospecha de diabetes mellitus tipo 2.",
  tratamiento: [
    "control nutricional",
    "actividad fisica supervisada",
    "valoracion medica para tratamiento farmacologico",
  ],
  explicacion:
    "Los sintomas y la presencia de hallazgos visuales como glucometro orientan a una enfermedad metabolica que requiere confirmacion con pruebas de laboratorio.",
};

export function buildSystemPrompt() {
  return `
Eres un sistema experto medico orientado a apoyo educativo y triage preliminar.
Debes responder SIEMPRE con un objeto json valido y nada mas.
No uses markdown.
No uses bloques de codigo.
No agregues texto antes ni despues del json.
Usa exactamente estas claves en este orden:
enfermedad, tipo, sintomas, pruebas, diagnostico, tratamiento, explicacion.

Reglas:
1. El json debe ser valido.
2. "sintomas", "pruebas" y "tratamiento" deben ser arreglos de strings.
3. El arbol debe reflejar una jerarquia clinica minima de 5 niveles: enfermedad -> tipo -> sintomas -> pruebas -> diagnostico -> tratamiento.
4. Responde en espanol claro.
5. No afirmes certeza absoluta si faltan datos; expresa sospecha clinica razonable.
6. La explicacion debe conectar sintomas, pruebas sugeridas, diagnostico y tratamiento.

Ejemplo de json esperado:
${JSON.stringify(RESPONSE_EXAMPLE, null, 2)}
`.trim();
}

export function buildUserPrompt(input) {
  const objetos =
    input.objetosDetectados.length > 0
      ? input.objetosDetectados.join(", ")
      : "ninguno";

  return `
Analiza el siguiente caso clinico y responde solo con json valido.

Datos del paciente:
- tipoEnfermedad: ${input.tipoEnfermedad}
- grupoEdad: ${input.grupoEdad}
- sexo: ${input.sexo}
- nivelUrgencia: ${input.nivelUrgencia}
- contextoClinico: ${input.contextoClinico}
- sintomas: ${input.sintomas.join(", ")}
- objetosDetectados: ${objetos}

Instrucciones clinicas:
- Usa los objetosDetectados como evidencia complementaria cuando sea razonable.
- Si se detecta "glucometro", "jeringa" o "pastillas", relaciona ese hallazgo con la sospecha medica de forma prudente.
- Sugiere pruebas coherentes con el tipo de enfermedad.
- Mantente dentro del esquema json requerido.
`.trim();
}

export function buildRepairPrompt(reason) {
  return `
La respuesta anterior no fue aceptada.
Motivo: ${reason}

Devuelve nuevamente solo un objeto json valido.
No incluyas markdown.
No incluyas comentarios.
No incluyas claves adicionales.
`.trim();
}

