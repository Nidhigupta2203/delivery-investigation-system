import type {
  Delivery,
  DeliveryCreate,
  DeliveryStatus,
  DeliveryStatusUpdate,
  ManifestCreate,
  ManifestResponse,
  TransferJob,
} from '../types/api'
import { apiClient } from './client'

export const deliveriesApi = {
  list: (params?: { order_id?: string; status?: DeliveryStatus; skip?: number; limit?: number }) =>
    apiClient.get<Delivery[]>('/deliveries', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Delivery>(`/deliveries/${id}`).then((r) => r.data),

  create: (data: DeliveryCreate) =>
    apiClient.post<Delivery>('/deliveries', data).then((r) => r.data),

  updateStatus: (id: string, data: DeliveryStatusUpdate) =>
    apiClient.patch<Delivery>(`/deliveries/${id}/status`, data).then((r) => r.data),

  // Manifest
  registerManifest: (id: string, data: ManifestCreate) =>
    apiClient.post<ManifestResponse>(`/deliveries/${id}/manifest`, data).then((r) => r.data),

  getManifest: (id: string) =>
    apiClient.get<ManifestResponse>(`/deliveries/${id}/manifest`).then((r) => r.data),

  // Transfer
  startTransfer: (id: string) =>
    apiClient.post<TransferJob>(`/deliveries/${id}/transfer`).then((r) => r.data),

  getTransferStatus: (id: string) =>
    apiClient.get<TransferJob>(`/deliveries/${id}/transfer-status`).then((r) => r.data),

  retryTransfer: (id: string) =>
    apiClient.post<TransferJob>(`/deliveries/${id}/retry-transfer`).then((r) => r.data),
}
