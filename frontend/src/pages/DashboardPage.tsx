import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { organizationsApi } from '../api/organizations'
import { customersApi } from '../api/customers'
import { ordersApi } from '../api/orders'
import { deliveriesApi } from '../api/deliveries'
import { Card, CardBody } from '../components/ui/Card'
import { LoadingState } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { extractErrorMessage } from '../api/client'
import type { DeliveryStatus } from '../types/api'

function StatCard({ label, value, to, color }: { label: string; value: number | string; to: string; color: string }) {
  return (
    <Link to={to}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardBody>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
        </CardBody>
      </Card>
    </Link>
  )
}

export function DashboardPage() {
  const orgsQuery   = useQuery({ queryKey: ['organizations'], queryFn: () => organizationsApi.list() })
  const custsQuery  = useQuery({ queryKey: ['customers'],     queryFn: () => customersApi.list() })
  const ordersQuery = useQuery({ queryKey: ['orders'],        queryFn: () => ordersApi.list() })
  const delsQuery   = useQuery({ queryKey: ['deliveries'],    queryFn: () => deliveriesApi.list() })

  const isLoading = orgsQuery.isLoading || custsQuery.isLoading || ordersQuery.isLoading || delsQuery.isLoading
  const error     = orgsQuery.error || custsQuery.error || ordersQuery.error || delsQuery.error

  if (isLoading) return <LoadingState message="Loading dashboard…" />
  if (error)     return <ErrorMessage message={extractErrorMessage(error)} />

  const deliveries = delsQuery.data ?? []
  const statusGroups = deliveries.reduce<Record<string, number>>((acc, d) => {
    acc[d.status] = (acc[d.status] ?? 0) + 1
    return acc
  }, {})

  const statusColors: Record<DeliveryStatus, string> = {
    PLANNED:      'bg-gray-100 text-gray-700',
    TRANSFERRING: 'bg-blue-100 text-blue-700',
    TRANSFERRED:  'bg-indigo-100 text-indigo-700',
    ACCEPTED:     'bg-green-100 text-green-700',
    REJECTED:     'bg-red-100 text-red-700',
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-sm text-gray-500 mt-1">Overview of the Delivery Investigation System</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Organizations" value={orgsQuery.data?.length ?? 0}  to="/organizations" color="text-blue-600" />
        <StatCard label="Customers"     value={custsQuery.data?.length ?? 0}  to="/customers"     color="text-purple-600" />
        <StatCard label="Orders"        value={ordersQuery.data?.length ?? 0} to="/orders"        color="text-orange-600" />
        <StatCard label="Deliveries"    value={delsQuery.data?.length ?? 0}   to="/deliveries"    color="text-green-600" />
      </div>

      {/* Delivery status summary */}
      <Card>
        <CardBody>
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Delivery Status Summary</h3>
          {deliveries.length === 0 ? (
            <p className="text-sm text-gray-400">No deliveries yet.</p>
          ) : (
            <div className="flex flex-wrap gap-3">
              {(Object.entries(statusGroups) as [DeliveryStatus, number][]).map(([status, count]) => (
                <span
                  key={status}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${statusColors[status]}`}
                >
                  {status}
                  <span className="font-bold">{count}</span>
                </span>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Quick links */}
      <Card>
        <CardBody>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h3>
          <div className="flex flex-wrap gap-3">
            <Link to="/organizations" className="text-sm text-blue-600 hover:underline">+ New Organization</Link>
            <Link to="/customers"     className="text-sm text-blue-600 hover:underline">+ New Customer</Link>
            <Link to="/orders"        className="text-sm text-blue-600 hover:underline">+ New Order</Link>
            <Link to="/deliveries"    className="text-sm text-blue-600 hover:underline">+ New Delivery</Link>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
