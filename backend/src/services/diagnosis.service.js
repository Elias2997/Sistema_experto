import { env } from "../config/env.js";
import {
  buildRepairPrompt,
  buildSystemPrompt,
  buildUserPrompt,
} from "../prompts/medicalPrompt.js";
import { parseJsonObject } from "../utils/json.js";
import { AppError } from "../utils/appError.js";
import { validateDiagnosisTree } from "../validators/response.validator.js";
import { callDeepSeekChat } from "./deepseek.client.js";
import { generateRuleBasedDiagnosis } from "./ruleBasedDiagnosis.service.js";

export async function generateDiagnosis(input) {
  if (!env.llmApiKey) {
    return generateRuleBasedDiagnosis(
      input,
      `no se configuro la API key de ${env.llmProviderName}`,
    );
  }

  const messages = [
    { role: "system", content: buildSystemPrompt() },
    { role: "user", content: buildUserPrompt(input) },
  ];

  for (let attempt = 1; attempt <= env.maxRetries; attempt += 1) {
    let response;

    try {
      response = await callDeepSeekChat(messages);
    } catch (error) {
      if (
        error instanceof AppError &&
        [
          "LLM_CONNECTION_ERROR",
          "LLM_TIMEOUT",
          "LLM_API_ERROR",
          "LLM_INVALID_RESPONSE",
          "LLM_EMPTY_CONTENT",
        ].includes(error.code)
      ) {
        const reason =
          error.details?.providerMessage ||
          error.details?.motivo ||
          error.message.toLowerCase();

        return generateRuleBasedDiagnosis(input, reason);
      }

      throw error;
    }

    try {
      const parsed = parseJsonObject(response.content);
      const diagnosis = validateDiagnosisTree(parsed);

      return {
        diagnosis,
        attempts: attempt,
        model: env.llmModel,
        usage: response.usage,
      };
    } catch (error) {
      if (attempt === env.maxRetries) {
        return generateRuleBasedDiagnosis(
          input,
          `el proveedor devolvio una salida invalida tras ${attempt} intentos: ${error.message.toLowerCase()}`,
        );
      } 

      messages.push({
        role: "assistant",
        content: response.content || "{}",
      });
      messages.push({
        role: "user",
        content: buildRepairPrompt(error.message),
      });
    }
  }

  throw new AppError(
    500,
    "No se pudo completar el diagnostico por una condicion inesperada.",
    "UNREACHABLE_STATE",
  );
}
