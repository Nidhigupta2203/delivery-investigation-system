import axios, { type AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** Extract a human-readable error message from an Axios error. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail: string }>
    const detail = axiosErr.response?.data?.detail
    if (detail) return detail
    if (axiosErr.response?.status === 404) return 'Resource not found.'
    if (axiosErr.response?.status === 409) return 'A conflict occurred (duplicate entry).'
    if (axiosErr.response?.status === 400) return 'Invalid request.'
    if (axiosErr.message) return axiosErr.message
  }
  if (error instanceof Error) return error.message
  return 'An unexpected error occurred.'
}
