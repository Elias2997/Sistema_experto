import { Router } from "express";

import { createDiagnosis } from "../controllers/diagnostico.controller.js";

const router = Router();

router.get("/", (_req, res) => {
  res.json({
    ok: true,
    message: "Usa POST /diagnostico para generar un diagnostico clinico.",
    ejemplo: {
      sintomas: ["fatiga"],
      tipoEnfermedad: "general",
      grupoEdad: "adulto",
      sexo: "otro",
      nivelUrgencia: "media",
      contextoClinico: "consulta general",
    },
  });
});

router.post("/", createDiagnosis);

export default router;
