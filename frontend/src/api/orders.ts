import type { Order, OrderCreate, OrderStatus, OrderStatusUpdate } from '../types/api'
import { apiClient } from './client'

export const ordersApi = {
  list: (params?: { customer_id?: string; status?: OrderStatus; skip?: number; limit?: number }) =>
    apiClient.get<Order[]>('/orders', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Order>(`/orders/${id}`).then((r) => r.data),

  create: (data: OrderCreate) =>
    apiClient.post<Order>('/orders', data).then((r) => r.data),

  updateStatus: (id: string, data: OrderStatusUpdate) =>
    apiClient.patch<Order>(`/orders/${id}/status`, data).then((r) => r.data),
}
