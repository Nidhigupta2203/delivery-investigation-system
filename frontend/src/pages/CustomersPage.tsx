import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { customersApi } from '../api/customers'
import { organizationsApi } from '../api/organizations'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input, Select } from '../components/ui/FormField'
import { LoadingState } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { EmptyState } from '../components/ui/EmptyState'
import { extractErrorMessage } from '../api/client'
import type { Customer } from '../types/api'

function CreateCustomerForm({ onSuccess }: { onSuccess: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [orgId, setOrgId] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const orgsQuery = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.list(),
  })

  const mutation = useMutation({
    mutationFn: () => customersApi.create({ organization_id: orgId, name, email }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['customers'] })
      setName('')
      setEmail('')
      setOrgId('')
      setFormError(null)
      onSuccess()
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }} className="space-y-4">
      {formError && <ErrorMessage message={formError} />}
      <Select label="Organization" value={orgId} onChange={(e) => setOrgId(e.target.value)} required>
        <option value="">Select organization…</option>
        {orgsQuery.data?.map((o) => (
          <option key={o.id} value={o.id}>{o.name}</option>
        ))}
      </Select>
      <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required placeholder="Jane Smith" />
      <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="jane@example.com" />
      <div className="flex justify-end">
        <Button type="submit" loading={mutation.isPending}>Create Customer</Button>
      </div>
    </form>
  )
}

export function CustomersPage() {
  const [showForm, setShowForm] = useState(false)
  const [filterOrgId, setFilterOrgId] = useState('')

  const orgsQuery = useQuery({ queryKey: ['organizations'], queryFn: () => organizationsApi.list() })
  const { data, isLoading, error } = useQuery({
    queryKey: ['customers', filterOrgId],
    queryFn: () => customersApi.list(filterOrgId ? { organization_id: filterOrgId } : undefined),
  })

  const orgMap = Object.fromEntries((orgsQuery.data ?? []).map((o) => [o.id, o.name]))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Customers</h2>
          <p className="text-sm text-gray-500 mt-1">Manage customer accounts</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Customer'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><h3 className="text-sm font-semibold text-gray-700">Create Customer</h3></CardHeader>
          <CardBody><CreateCustomerForm onSuccess={() => setShowForm(false)} /></CardBody>
        </Card>
      )}

      {/* Filter */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600">Filter by Organization:</label>
        <select
          value={filterOrgId}
          onChange={(e) => setFilterOrgId(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All organizations</option>
          {orgsQuery.data?.map((o) => (
            <option key={o.id} value={o.id}>{o.name}</option>
          ))}
        </select>
      </div>

      <Card>
        {isLoading && <LoadingState />}
        {error && <CardBody><ErrorMessage message={extractErrorMessage(error)} /></CardBody>}
        {data && data.length === 0 && <EmptyState title="No customers" message="Create a customer to get started." />}
        {data && data.length > 0 && (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Email</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Organization</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((customer: Customer) => (
                <tr key={customer.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 text-sm font-medium text-gray-900">{customer.name}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{customer.email}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{orgMap[customer.organization_id] ?? '—'}</td>
                  <td className="px-6 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${customer.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {customer.is_active ? 'Active' : 'Inactive'}
                    </span>
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
