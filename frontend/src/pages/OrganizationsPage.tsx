import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { organizationsApi } from '../api/organizations'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/FormField'
import { LoadingState } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { EmptyState } from '../components/ui/EmptyState'
import { extractErrorMessage } from '../api/client'
import type { Organization } from '../types/api'

function OrganizationRow({ org, onSelect }: { org: Organization; onSelect: (o: Organization) => void }) {
  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer"
      onClick={() => onSelect(org)}
    >
      <td className="px-6 py-3 text-sm text-gray-900 font-medium">{org.name}</td>
      <td className="px-6 py-3 text-sm text-gray-500 font-mono">{org.code}</td>
      <td className="px-6 py-3">
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${org.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {org.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-6 py-3 text-xs text-gray-400">
        {new Date(org.created_at).toLocaleDateString()}
      </td>
    </tr>
  )
}

function CreateOrgForm({ onSuccess }: { onSuccess: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => organizationsApi.create({ name, code }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['organizations'] })
      setName('')
      setCode('')
      setFormError(null)
      onSuccess()
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  })

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
      className="space-y-4"
    >
      {formError && <ErrorMessage message={formError} />}
      <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required placeholder="Acme Corp" />
      <Input label="Code" value={code} onChange={(e) => setCode(e.target.value)} required placeholder="acme-corp" />
      <div className="flex justify-end gap-2">
        <Button type="submit" loading={mutation.isPending}>Create Organization</Button>
      </div>
    </form>
  )
}

function OrgDetailPanel({ org, onClose }: { org: Organization; onClose: () => void }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800">Organization Details</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>
      </CardHeader>
      <CardBody className="space-y-3">
        <Detail label="ID"      value={org.id} mono />
        <Detail label="Name"    value={org.name} />
        <Detail label="Code"    value={org.code} mono />
        <Detail label="Status"  value={org.is_active ? 'Active' : 'Inactive'} />
        <Detail label="Created" value={new Date(org.created_at).toLocaleString()} />
        <Detail label="Updated" value={new Date(org.updated_at).toLocaleString()} />
      </CardBody>
    </Card>
  )
}

function Detail({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
      <p className={`text-sm text-gray-800 break-all ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  )
}

export function OrganizationsPage() {
  const [showForm, setShowForm] = useState(false)
  const [selected, setSelected] = useState<Organization | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.list(),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Organizations</h2>
          <p className="text-sm text-gray-500 mt-1">Manage customer organizations</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Organization'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><h3 className="text-sm font-semibold text-gray-700">Create Organization</h3></CardHeader>
          <CardBody>
            <CreateOrgForm onSuccess={() => setShowForm(false)} />
          </CardBody>
        </Card>
      )}

      <div className="flex gap-6">
        <div className="flex-1">
          <Card>
            {isLoading && <LoadingState />}
            {error && <CardBody><ErrorMessage message={extractErrorMessage(error)} /></CardBody>}
            {data && data.length === 0 && <EmptyState title="No organizations yet" message="Create your first organization to get started." />}
            {data && data.length > 0 && (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
                    <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Code</th>
                    <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                    <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.map((org) => (
                    <OrganizationRow key={org.id} org={org} onSelect={setSelected} />
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </div>

        {selected && (
          <div className="w-80 flex-shrink-0">
            <OrgDetailPanel org={selected} onClose={() => setSelected(null)} />
          </div>
        )}
      </div>
    </div>
  )
}
