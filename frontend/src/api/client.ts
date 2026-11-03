import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** Extract a human-readable error message from an Axios error. */
export function extractErrorMessage(error: unknown): string {
  const err = error as any;

  const detail = err?.response?.data?.detail ?? err?.response?.data?.message;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const loc = Array.isArray(item.loc) ? item.loc.join(" → ") : "";

        return `${loc}: ${item.msg ?? "Validation error"}`;
      })
      .join("\n");
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (err?.message) {
    return err.message;
  }

  return "Something went wrong.";
}
