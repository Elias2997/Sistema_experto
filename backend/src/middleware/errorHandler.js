import { AppError } from "../utils/appError.js";

export function notFoundHandler(req, res) {
  res.status(404).json({
    ok: false,
    error: {
      code: "NOT_FOUND",
      message: `Ruta no encontrada: ${req.method} ${req.originalUrl}`,
    },
  });
}

export function errorHandler(error, _req, res, _next) {
  if (error instanceof SyntaxError && "body" in error) {
    return res.status(400).json({
      ok: false,
      error: {
        code: "INVALID_JSON",
        message: "El cuerpo de la solicitud no contiene JSON valido.",
      },
    });
  }

  const normalizedError =
    error instanceof AppError
      ? error
      : new AppError(
          500,
          "Ocurrio un error interno procesando el diagnostico.",
          "INTERNAL_ERROR",
        );

  if (normalizedError.statusCode >= 500) {
    console.error(error);
  }

  return res.status(normalizedError.statusCode).json({
    ok: false,
    error: {
      code: normalizedError.code,
      message: normalizedError.message,
      details: normalizedError.details,
    },
  });
}

