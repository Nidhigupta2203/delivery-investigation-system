import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ordersApi } from '../api/orders'
import { customersApi } from '../api/customers'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input, Select } from '../components/ui/FormField'
import { OrderStatusBadge } from '../components/ui/StatusBadge'
import { LoadingState } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { EmptyState } from '../components/ui/EmptyState'
import { extractErrorMessage } from '../api/client'
import type { Order, OrderStatus } from '../types/api'

function CreateOrderForm({ onSuccess }: { onSuccess: () => void }) {
  const qc = useQueryClient()
  const [customerId, setCustomerId] = useState('')
  const [orderNumber, setOrderNumber] = useState('')
  const [count, setCount] = useState('0')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const custsQuery = useQuery({ queryKey: ['customers'], queryFn: () => customersApi.list() })

  const mutation = useMutation({
    mutationFn: () => ordersApi.create({
      customer_id: customerId,
      order_number: orderNumber,
      requested_recordings_count: parseInt(count, 10),
      description: description || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['orders'] })
      setCustomerId('')
      setOrderNumber('')
      setCount('0')
      setDescription('')
      setFormError(null)
      onSuccess()
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }} className="space-y-4">
      {formError && <ErrorMessage message={formError} />}
      <Select label="Customer" value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
        <option value="">Select customer…</option>
        {custsQuery.data?.map((c) => (
          <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
        ))}
      </Select>
      <Input label="Order Number" value={orderNumber} onChange={(e) => setOrderNumber(e.target.value)} required placeholder="ORD-2026-001" />
      <Input label="Requested Recordings" type="number" min="0" value={count} onChange={(e) => setCount(e.target.value)} />
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">Description</label>
        <textarea
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional notes…"
        />
      </div>
      <div className="flex justify-end">
        <Button type="submit" loading={mutation.isPending}>Create Order</Button>
      </div>
    </form>
  )
}

const STATUS_OPTIONS: OrderStatus[] = ['PENDING', 'IN_PROGRESS', 'FULFILLED', 'CANCELLED']

export function OrdersPage() {
  const [showForm, setShowForm] = useState(false)
  const [filterStatus, setFilterStatus] = useState<OrderStatus | ''>('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['orders', filterStatus],
    queryFn: () => ordersApi.list(filterStatus ? { status: filterStatus as OrderStatus } : undefined),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Orders</h2>
          <p className="text-sm text-gray-500 mt-1">Manage dataset recording orders</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Order'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><h3 className="text-sm font-semibold text-gray-700">Create Order</h3></CardHeader>
          <CardBody><CreateOrderForm onSuccess={() => setShowForm(false)} /></CardBody>
        </Card>
      )}

      {/* Filter */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600">Filter by Status:</label>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as OrderStatus | '')}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
      </div>

      <Card>
        {isLoading && <LoadingState />}
        {error && <CardBody><ErrorMessage message={extractErrorMessage(error)} /></CardBody>}
        {data && data.length === 0 && <EmptyState title="No orders found" message="Create an order to get started." />}
        {data && data.length > 0 && (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Order #</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Recordings Requested</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((order: Order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 text-sm font-medium text-gray-900 font-mono">{order.order_number}</td>
                  <td className="px-6 py-3"><OrderStatusBadge status={order.status} /></td>
                  <td className="px-6 py-3 text-sm text-gray-600">{order.requested_recordings_count}</td>
                  <td className="px-6 py-3 text-xs text-gray-400">{new Date(order.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
