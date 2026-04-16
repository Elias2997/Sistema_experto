function assertString(value, fieldName) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`El campo "${fieldName}" debe ser un texto no vacio.`);
  }

  return value.trim();
}

function assertStringArray(value, fieldName) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`El campo "${fieldName}" debe ser un arreglo con elementos.`);
  }

  return value.map((item) => assertString(item, fieldName));
}

export function validateDiagnosisTree(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("La respuesta del modelo debe ser un objeto JSON.");
  }

  return {
    enfermedad: assertString(payload.enfermedad, "enfermedad"),
    tipo: assertString(payload.tipo, "tipo"),
    sintomas: assertStringArray(payload.sintomas, "sintomas"),
    pruebas: assertStringArray(payload.pruebas, "pruebas"),
    diagnostico: assertString(payload.diagnostico, "diagnostico"),
    tratamiento: assertStringArray(payload.tratamiento, "tratamiento"),
    explicacion: assertString(payload.explicacion, "explicacion"),
  };
}
