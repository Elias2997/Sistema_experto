export function parseJsonObject(rawContent) {
  if (typeof rawContent !== "string" || rawContent.trim() === "") {
    throw new Error("La respuesta del modelo llego vacia.");
  }

  const cleaned = rawContent
    .replace(/```json/gi, "")
    .replace(/```/g, "")
    .trim();

  try {
    return JSON.parse(cleaned);
  } catch (_error) {
    const extracted = extractFirstJsonObject(cleaned);

    if (!extracted) {
      throw new Error("No se encontro un objeto JSON en la respuesta.");
    }

    try {
      return JSON.parse(extracted);
    } catch (_innerError) {
      throw new Error("No fue posible parsear el JSON devuelto por el modelo.");
    }
  }
}

function extractFirstJsonObject(text) {
  let depth = 0;
  let start = -1;
  let inString = false;
  let escaped = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];

    if (escaped) {
      escaped = false;
      continue;
    }

    if (char === "\\") {
      escaped = true;
      continue;
    }

    if (char === "\"") {
      inString = !inString;
      continue;
    }

    if (inString) {
      continue;
    }

    if (char === "{") {
      if (depth === 0) {
        start = index;
      }
      depth += 1;
    }

    if (char === "}") {
      depth -= 1;

      if (depth === 0 && start >= 0) {
        return text.slice(start, index + 1);
      }
    }
  }

  return null;
}

