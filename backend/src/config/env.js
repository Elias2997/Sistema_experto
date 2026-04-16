import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const envFilePath = path.resolve(currentDir, "../../.env");

dotenv.config({ path: envFilePath });

function toPositiveInteger(value, fallback) {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "";
}

function inferProviderName(baseUrl, explicitName) {
  if (explicitName?.trim()) {
    return explicitName.trim();
  }

  if (baseUrl.includes("openrouter.ai")) {
    return "OpenRouter";
  }

  if (baseUrl.includes("huggingface.co")) {
    return "Hugging Face";
  }

  if (baseUrl.includes("groq.com")) {
    return "Groq";
  }

  if (baseUrl.includes("deepseek.com")) {
    return "DeepSeek";
  }

  return "Proveedor LLM";
}

const llmApiKey = firstNonEmpty(
  process.env.LLM_API_KEY,
  process.env.DEEPSEEK_API_KEY,
);
const llmModel = firstNonEmpty(
  process.env.LLM_MODEL,
  process.env.DEEPSEEK_MODEL,
  "deepseek-chat",
);
const llmBaseUrl = firstNonEmpty(
  process.env.LLM_BASE_URL,
  process.env.DEEPSEEK_BASE_URL,
  "https://api.deepseek.com",
);
const llmProviderName = inferProviderName(
  llmBaseUrl,
  process.env.LLM_PROVIDER_NAME,
);

export const env = {
  port: toPositiveInteger(process.env.PORT, 3000),
  llmApiKey,
  llmModel,
  llmBaseUrl,
  llmProviderName,
  maxRetries: toPositiveInteger(process.env.DEEPSEEK_MAX_RETRIES, 3),
  requestTimeoutMs: toPositiveInteger(process.env.DEEPSEEK_TIMEOUT_MS, 45000),
  deepseekApiKey: llmApiKey,
  deepseekModel: llmModel,
  deepseekBaseUrl: llmBaseUrl,
};
