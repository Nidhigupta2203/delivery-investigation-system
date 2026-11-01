import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { deliveriesApi } from '../api/deliveries'
import { ordersApi } from '../api/orders'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input, Select } from '../components/ui/FormField'
import { DeliveryStatusBadge } from '../components/ui/StatusBadge'
import { LoadingState } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { EmptyState } from '../components/ui/EmptyState'
import { extractErrorMessage } from '../api/client'
import type { Delivery, DeliveryStatus } from '../types/api'

function CreateDeliveryForm({ onSuccess }: { onSuccess: () => void }) {
  const qc = useQueryClient()
  const [orderId, setOrderId] = useState('')
  const [deliveryNumber, setDeliveryNumber] = useState('')
  const [sourceLocation, setSourceLocation] = useState('')
  const [targetLocation, setTargetLocation] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const ordersQuery = useQuery({ queryKey: ['orders'], queryFn: () => ordersApi.list() })

  const mutation = useMutation({
    mutationFn: () => deliveriesApi.create({
      order_id: orderId,
      delivery_number: deliveryNumber,
      source_location: sourceLocation || undefined,
      target_location: targetLocation || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['deliveries'] })
      setOrderId('')
      setDeliveryNumber('')
      setSourceLocation('')
      setTargetLocation('')
      setFormError(null)
      onSuccess()
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }} className="space-y-4">
      {formError && <ErrorMessage message={formError} />}
      <Select label="Order" value={orderId} onChange={(e) => setOrderId(e.target.value)} required>
        <option value="">Select order…</option>
        {ordersQuery.data?.map((o) => (
          <option key={o.id} value={o.id}>{o.order_number}</option>
        ))}
      </Select>
      <Input label="Delivery Number" value={deliveryNumber} onChange={(e) => setDeliveryNumber(e.target.value)} required placeholder="DEL-001" />
      <Input label="Source Location (optional)" value={sourceLocation} onChange={(e) => setSourceLocation(e.target.value)} placeholder="source-bucket" />
      <Input label="Target Location (optional)" value={targetLocation} onChange={(e) => setTargetLocation(e.target.value)} placeholder="customer-bucket" />
      <div className="flex justify-end">
        <Button type="submit" loading={mutation.isPending}>Create Delivery</Button>
      </div>
    </form>
  )
}

const STATUS_OPTIONS: DeliveryStatus[] = ['PLANNED', 'TRANSFERRING', 'TRANSFERRED', 'ACCEPTED', 'REJECTED']

export function DeliveriesPage() {
  const [showForm, setShowForm] = useState(false)
  const [filterStatus, setFilterStatus] = useState<DeliveryStatus | ''>('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['deliveries', filterStatus],
    queryFn: () => deliveriesApi.list(filterStatus ? { status: filterStatus as DeliveryStatus } : undefined),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Deliveries</h2>
          <p className="text-sm text-gray-500 mt-1">Manage delivery batches and file transfers</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Delivery'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><h3 className="text-sm font-semibold text-gray-700">Create Delivery</h3></CardHeader>
          <CardBody><CreateDeliveryForm onSuccess={() => setShowForm(false)} /></CardBody>
        </Card>
      )}

      {/* Filter */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600">Filter by Status:</label>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as DeliveryStatus | '')}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <Card>
        {isLoading && <LoadingState />}
        {error && <CardBody><ErrorMessage message={extractErrorMessage(error)} /></CardBody>}
        {data && data.length === 0 && <EmptyState title="No deliveries found" message="Create a delivery batch for an order." />}
        {data && data.length > 0 && (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Delivery #</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Created</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((delivery: Delivery) => (
                <tr key={delivery.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 text-sm font-medium text-gray-900 font-mono">{delivery.delivery_number}</td>
                  <td className="px-6 py-3"><DeliveryStatusBadge status={delivery.status} /></td>
                  <td className="px-6 py-3 text-xs text-gray-400">{new Date(delivery.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-3">
                    <Link
                      to="/deliveries/$deliveryId"
                      params={{ deliveryId: delivery.id }}
                      className="text-sm text-blue-600 hover:underline font-medium"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
