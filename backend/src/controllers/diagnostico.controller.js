import { generateDiagnosis } from "../services/diagnosis.service.js";
import { validateDiagnosisInput } from "../validators/request.validator.js";

export async function createDiagnosis(req, res, next) {
  try {
    const input = validateDiagnosisInput(req.body);
    const result = await generateDiagnosis(input);

    res.json({
      ok: true,
      enfermedad: result.diagnosis.enfermedad,
      tipo: result.diagnosis.tipo,
      sintomas: result.diagnosis.sintomas,
      pruebas: result.diagnosis.pruebas,
      diagnostico: result.diagnosis.diagnostico,
      tratamiento: result.diagnosis.tratamiento,
      explicacion: result.diagnosis.explicacion,
      meta: {
        modelo: result.model,
        intentos: result.attempts,
        objetosDetectados: input.objetosDetectados,
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    next(error);
  }
}

