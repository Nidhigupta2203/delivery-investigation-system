import type { Customer, CustomerCreate } from '../types/api'
import { apiClient } from './client'

export const customersApi = {
  list: (params?: { organization_id?: string; skip?: number; limit?: number }) =>
    apiClient.get<Customer[]>('/customers', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Customer>(`/customers/${id}`).then((r) => r.data),

  create: (data: CustomerCreate) =>
    apiClient.post<Customer>('/customers', data).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/customers/${id}`),
}
