// DeliveryDetailPage.tsx - updated to fix manifest rendering and comment parsing
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { deliveriesApi } from '../api/deliveries'
import { ordersApi } from '../api/orders'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import {
  DeliveryStatusBadge,
  TransferJobStatusBadge,
  FileTransferStatusBadge,
  QualityStatusBadge,
} from '../components/ui/StatusBadge'
import { LoadingState } from '../components/ui/Spinner'
import { ManifestForm } from '../components/forms/ManifestForm'
import { CustomerReviewSection } from '../components/delivery/CustomerReviewSection'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { EmptyState } from '../components/ui/EmptyState'
import { extractErrorMessage } from '../api/client'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function ProgressBar({ percent }: { percent: number }) {
  const clamped = Math.min(100, Math.max(0, percent))
  return (
    <div className="w-full bg-gray-100 rounded-full h-2.5">
      <div
        className="bg-blue-500 h-2.5 rounded-full transition-all duration-500"
        style={{ width: `${clamped}%` }}
      />
    </div>
  )
}

function Detail({ label, value, mono = false }: { label: string; value: string | null | undefined; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
      <p className={`text-sm text-gray-800 break-all ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</p>
    </div>
  )
}

export function DeliveryDetailPage() {
  const { deliveryId } = useParams({ from: '/deliveries/$deliveryId' })
  const qc = useQueryClient()

  // Queries
  const deliveryQuery = useQuery({
    queryKey: ['delivery', deliveryId],
    queryFn: () => deliveriesApi.get(deliveryId),
  })

  const manifestQuery = useQuery({
    queryKey: ['manifest', deliveryId],
    queryFn: () => deliveriesApi.getManifest(deliveryId),
    retry: false,
  })

  const transferQuery = useQuery({
    queryKey: ['transfer-status', deliveryId],
    queryFn: () => deliveriesApi.getTransferStatus(deliveryId),
    retry: false,
    // Poll while in-progress
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'IN_PROGRESS' || status === 'PENDING' ? 2000 : false
    },
  })

  // Mutations
  const startTransfer = useMutation({
    mutationFn: () => deliveriesApi.startTransfer(deliveryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transfer-status', deliveryId] })
      qc.invalidateQueries({ queryKey: ['delivery', deliveryId] })
    },
  })

  const retryTransfer = useMutation({
    mutationFn: () => deliveriesApi.retryTransfer(deliveryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transfer-status', deliveryId] })
    },
  })

  const delivery = deliveryQuery.data
  const manifest = manifestQuery.data
  const transferJob = transferQuery.data

  // Look up order
  const orderQuery = useQuery({
    queryKey: ['order', delivery?.order_id],
    queryFn: () => ordersApi.get(delivery!.order_id),
    enabled: !!delivery?.order_id,
  })

  if (deliveryQuery.isLoading) return <LoadingState message="Loading delivery…" />
  if (deliveryQuery.error)
    return <ErrorMessage message={extractErrorMessage(deliveryQuery.error)} />
  if (!delivery) return <ErrorMessage message="Delivery not found." />

  const canStartTransfer =
    manifest &&
    manifest.total_recordings > 0 &&
    (delivery.status === 'PLANNED' || delivery.status === 'TRANSFERRED') &&
    !transferJob

  const canRetry =
    transferJob &&
    (transferJob.status === 'FAILED' || transferJob.status === 'COMPLETED') &&
    transferJob.file_transfers.some((ft) => ft.status === 'FAILED')

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 flex items-center gap-2">
        <Link to="/deliveries" className="hover:text-blue-600">Deliveries</Link>
        <span>/</span>
        <span className="font-mono text-gray-700">{delivery.delivery_number}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 font-mono">{delivery.delivery_number}</h2>
          <div className="flex items-center gap-3 mt-2">
            <DeliveryStatusBadge status={delivery.status} />
            {orderQuery.data && (
              <Link to="/orders" className="text-sm text-blue-600 hover:underline">
                Order: {orderQuery.data.order_number}
              </Link>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          <Link to="/deliveries/compare" search={{ baseId: delivery.id }}>
            <Button variant="secondary">
              ⚖️ Compare
            </Button>
          </Link>
          {canStartTransfer && (
            <Button onClick={() => startTransfer.mutate()} loading={startTransfer.isPending}>
              ▶ Start Transfer
            </Button>
          )}
          {canRetry && (
            <Button variant="secondary" onClick={() => retryTransfer.mutate()} loading={retryTransfer.isPending}>
              🔄 Retry Failed
            </Button>
          )}
        </div>
      </div>

      {/* Start / retry errors */}
      {startTransfer.error && (
        <ErrorMessage message={extractErrorMessage(startTransfer.error)} />
      )}
      {retryTransfer.error && (
        <ErrorMessage message={extractErrorMessage(retryTransfer.error)} />
      )}

      {/* Customer Review Section */}
      <CustomerReviewSection delivery={delivery} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delivery info */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-gray-700">Delivery Information</h3>
          </CardHeader>
          <CardBody className="space-y-3">
            <Detail label="ID" value={delivery.id} mono />
            <Detail label="Order ID" value={delivery.order_id} mono />
            <Detail label="Source Location" value={delivery.source_location} />
            <Detail label="Target Location" value={delivery.target_location} />
            {delivery.rejection_reason && (
              <Detail label="Rejection Reason" value={delivery.rejection_reason} />
            )}
            {delivery.decision_notes && (
              <Detail label="Decision Notes" value={delivery.decision_notes} />
            )}
            {delivery.accepted_at && (
              <Detail label="Accepted At" value={new Date(delivery.accepted_at).toLocaleString()} />
            )}
            {delivery.rejected_at && (
              <Detail label="Rejected At" value={new Date(delivery.rejected_at).toLocaleString()} />
            )}
            <Detail label="Created" value={new Date(delivery.created_at).toLocaleString()} />
          </CardBody>
        </Card>

        {/* Transfer Progress */}
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-gray-700">Transfer Progress</h3>
          </CardHeader>
          <CardBody>
            {transferQuery.isLoading && <LoadingState message="Loading transfer status…" />}
            {!transferJob && !transferQuery.isLoading && (
              <div className="text-center py-6 text-gray-400 text-sm">
                {manifest && manifest.total_recordings > 0
                  ? 'No transfer started yet. Click "Start Transfer" to begin.'
                  : 'Register a manifest first, then start transfer.'}
              </div>
            )}
            {transferJob && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <TransferJobStatusBadge status={transferJob.status} />
                  <span className="text-sm font-bold text-blue-600">{transferJob.progress_percentage.toFixed(1)}%</span>
                </div>
                <ProgressBar percent={transferJob.progress_percentage} />
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-400">Files</p>
                    <p className="font-medium">{transferJob.transferred_files} / {transferJob.total_files}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Bytes</p>
                    <p className="font-medium">{formatBytes(transferJob.transferred_bytes)} / {formatBytes(transferJob.total_bytes)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Retry Count</p>
                    <p className="font-medium">{transferJob.retry_count}</p>
                  </div>
                  {transferJob.error_message && (
                    <div className="col-span-2">
                      <p className="text-xs text-red-400">Error</p>
                      <p className="text-red-600 text-xs">{transferJob.error_message}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Manifest recordings */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700">Manifest Recordings</h3>
            {manifest && (
              <span className="text-xs text-gray-400">
                {manifest.total_recordings} recordings · {formatBytes(manifest.total_bytes)}
              </span>
            )}
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {manifestQuery.isLoading && <LoadingState />}
          {manifestQuery.error && (
            <ErrorMessage message={extractErrorMessage(manifestQuery.error)} />
          )}
          {/* No manifest – show registration form */}
          {(!manifest || manifest.total_recordings === 0) && !manifestQuery.isLoading && (
            <ManifestForm deliveryId={deliveryId as string} />
          )}
          {/* Manifest exists with zero recordings – empty state */}
          {manifest && manifest.total_recordings > 0 && manifest.recordings.length === 0 && (
            <EmptyState title="Manifest is empty" message="No recordings registered in this manifest." />
          )}
          {/* Manifest with recordings */}
          {manifest && manifest.recordings && manifest.recordings.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Recording ID</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">File Name</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Size</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">SHA-256</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Quality</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {manifest.recordings.map((rec) => (
                    <tr key={rec.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-700">{rec.recording_id}</td>
                      <td className="px-4 py-3 text-gray-800">{rec.file_name}</td>
                      <td className="px-4 py-3 text-gray-500 tabular-nums">{formatBytes(rec.file_size_bytes)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-400 max-w-[120px] truncate" title={rec.checksum_sha256 ?? ''}>
                        {rec.checksum_sha256 ? rec.checksum_sha256.slice(0, 16) + '…' : '—'}
                      </td>
                      <td className="px-4 py-3"><QualityStatusBadge status={rec.quality_status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Individual file transfer status */}
      {transferJob && transferJob.file_transfers.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold text-gray-700">Individual File Transfers</h3>
          </CardHeader>
          <CardBody className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Source Key</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Size</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Checksum ✓</th>
                    <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {transferJob.file_transfers.map((ft) => (
                    <tr key={ft.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-600 max-w-[200px] truncate" title={ft.source_key}>{ft.source_key}</td>
                      <td className="px-4 py-3"><FileTransferStatusBadge status={ft.status} /></td>
                      <td className="px-4 py-3 text-gray-500 tabular-nums">{formatBytes(ft.file_size_bytes)}</td>
                      <td className="px-4 py-3">
                        {ft.actual_checksum
                          ? ft.actual_checksum === ft.expected_checksum
                            ? <span className="text-green-600 text-xs">✓ Match</span>
                            : <span className="text-red-600 text-xs">✗ Mismatch</span>
                          : <span className="text-gray-400 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3 text-xs text-red-500 max-w-[180px] truncate" title={ft.error_message ?? ''}>
                        {ft.error_message ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
