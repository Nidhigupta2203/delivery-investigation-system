import type { Organization, OrganizationCreate, OrganizationUpdate } from '../types/api'
import { apiClient } from './client'

export const organizationsApi = {
  list: (params?: { skip?: number; limit?: number; is_active?: boolean }) =>
    apiClient.get<Organization[]>('/organizations', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Organization>(`/organizations/${id}`).then((r) => r.data),

  create: (data: OrganizationCreate) =>
    apiClient.post<Organization>('/organizations', data).then((r) => r.data),

  update: (id: string, data: OrganizationUpdate) =>
    apiClient.patch<Organization>(`/organizations/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/organizations/${id}`),
}
