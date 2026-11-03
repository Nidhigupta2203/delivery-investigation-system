import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearch } from '@tanstack/react-router'
import { deliveriesApi } from '../api/deliveries'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Select, Input } from '../components/ui/FormField'
import {
  ComparisonDiffTypeBadge,
  DeliveryStatusBadge,
  QualityStatusBadge,
} from '../components/ui/StatusBadge'
import { LoadingState } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { EmptyState } from '../components/ui/EmptyState'
import { extractErrorMessage } from '../api/client'
import type { ComparisonDiffType, DeliveryComparisonItem } from '../types/api'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const isNegative = bytes < 0
  const absBytes = Math.abs(bytes)
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(absBytes) / Math.log(1024))
  const formatted = `${(absBytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
  return isNegative ? `-${formatted}` : formatted
}

export function DeliveryComparisonPage() {
  const searchParams = useSearch({ strict: false }) as { baseId?: string; targetId?: string }
  const [baseId, setBaseId] = useState<string>(searchParams.baseId ?? '')
  const [targetId, setTargetId] = useState<string>(searchParams.targetId ?? '')
  const [diffFilter, setDiffFilter] = useState<ComparisonDiffType | 'ALL'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Load all deliveries for selection
  const deliveriesQuery = useQuery({
    queryKey: ['deliveries'],
    queryFn: () => deliveriesApi.list(),
  })

  // Compare query
  const canCompare = Boolean(baseId && targetId)
  const comparisonQuery = useQuery({
    queryKey: ['delivery-comparison', baseId, targetId],
    queryFn: () => deliveriesApi.compare(baseId, targetId),
    enabled: canCompare,
  })

  const deliveries = deliveriesQuery.data ?? []
  const comparison = comparisonQuery.data

  const handleSwap = () => {
    const temp = baseId
    setBaseId(targetId)
    setTargetId(temp)
  }

  // Filter items
  const filteredItems = (comparison?.items ?? []).filter((item: DeliveryComparisonItem) => {
    if (diffFilter !== 'ALL' && item.diff_type !== diffFilter) {
      return false
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchId = item.recording_id.toLowerCase().includes(q)
      const matchFile = item.file_name.toLowerCase().includes(q)
      if (!matchId && !matchFile) return false
    }
    return true
  })

  return (
    <div className="space-y-6">
      {/* Breadcrumb & Navigation */}
      <nav className="text-sm text-gray-500 flex items-center gap-2">
        <Link to="/deliveries" className="hover:text-blue-600">Deliveries</Link>
        <span>/</span>
        <span className="text-gray-800 font-medium">Compare Deliveries</span>
      </nav>

      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Delivery Version Comparison</h2>
        <p className="text-sm text-gray-500 mt-1">
          Detect added, removed, and modified recordings, checksum discrepancies, and quality transitions between delivery batches.
        </p>
      </div>

      {/* Selector Card */}
      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold text-gray-700">Select Deliveries to Compare</h3>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
            <div className="md:col-span-2">
              <Select
                label="Base Delivery (Version A)"
                value={baseId}
                onChange={(e) => setBaseId(e.target.value)}
              >
                <option value="">Select base delivery…</option>
                {deliveries.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.delivery_number} ({d.status}) - {new Date(d.created_at).toLocaleDateString()}
                  </option>
                ))}
              </Select>
            </div>

            <div className="flex justify-center pb-1">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSwap}
                disabled={!baseId || !targetId}
                title="Swap Base and Target"
              >
                ⇄ Swap
              </Button>
            </div>

            <div className="md:col-span-2">
              <Select
                label="Target Delivery (Version B)"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
              >
                <option value="">Select target delivery…</option>
                {deliveries.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.delivery_number} ({d.status}) - {new Date(d.created_at).toLocaleDateString()}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Loading & Errors */}
      {comparisonQuery.isLoading && <LoadingState message="Computing delivery differences…" />}
      {comparisonQuery.error && (
        <ErrorMessage message={extractErrorMessage(comparisonQuery.error)} />
      )}

      {/* Initial state before selection */}
      {!canCompare && !comparisonQuery.isLoading && (
        <EmptyState
          title="Select Two Deliveries"
          message="Choose a base delivery and a target delivery above to analyze recordings and checksum differences."
        />
      )}

      {/* Comparison View */}
      {comparison && (
        <div className="space-y-6">
          {/* Deliveries Overview Header */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50/60 border border-blue-200 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-blue-700">Base Delivery (A)</span>
                <DeliveryStatusBadge status={comparison.base_delivery.status} />
              </div>
              <p className="text-xl font-bold font-mono text-gray-900">{comparison.base_delivery.delivery_number}</p>
              <div className="text-xs text-gray-600 flex gap-4">
                <span>Recordings: <strong>{comparison.base_delivery.total_recordings}</strong></span>
                <span>Size: <strong>{formatBytes(comparison.base_delivery.total_bytes)}</strong></span>
              </div>
            </div>

            <div className="bg-purple-50/60 border border-purple-200 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-purple-700">Target Delivery (B)</span>
                <DeliveryStatusBadge status={comparison.target_delivery.status} />
              </div>
              <p className="text-xl font-bold font-mono text-gray-900">{comparison.target_delivery.delivery_number}</p>
              <div className="text-xs text-gray-600 flex gap-4">
                <span>Recordings: <strong>{comparison.target_delivery.total_recordings}</strong></span>
                <span>Size: <strong>{formatBytes(comparison.target_delivery.total_bytes)}</strong></span>
              </div>
            </div>
          </div>

          {/* Metrics summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Added</p>
              <p className="text-xl font-bold text-green-600 mt-1">+{comparison.summary.added_count}</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Removed</p>
              <p className="text-xl font-bold text-red-600 mt-1">-{comparison.summary.removed_count}</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Changed</p>
              <p className="text-xl font-bold text-amber-600 mt-1">{comparison.summary.changed_count}</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Checksum Mismatches</p>
              <p className="text-xl font-bold text-red-700 mt-1">{comparison.summary.checksum_mismatches_count}</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Unchanged</p>
              <p className="text-xl font-bold text-gray-600 mt-1">{comparison.summary.unchanged_count}</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 font-medium">Net Size Delta</p>
              <p className={`text-xl font-bold mt-1 ${comparison.summary.size_delta_bytes >= 0 ? 'text-blue-600' : 'text-purple-600'}`}>
                {comparison.summary.size_delta_bytes > 0 ? '+' : ''}
                {formatBytes(comparison.summary.size_delta_bytes)}
              </p>
            </div>
          </div>

          {/* Filter and Search Bar */}
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Diff Type Filter Tabs */}
                <div className="flex flex-wrap gap-1 bg-gray-100 p-1 rounded-lg">
                  {(['ALL', 'CHANGED', 'ADDED', 'REMOVED', 'UNCHANGED'] as const).map((type) => {
                    const count =
                      type === 'ALL'
                        ? comparison.items.length
                        : type === 'CHANGED'
                          ? comparison.summary.changed_count
                          : type === 'ADDED'
                            ? comparison.summary.added_count
                            : type === 'REMOVED'
                              ? comparison.summary.removed_count
                              : comparison.summary.unchanged_count
                    return (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setDiffFilter(type)}
                        className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                          diffFilter === type
                            ? 'bg-white text-gray-900 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        {type} ({count})
                      </button>
                    )
                  })}
                </div>

                {/* Search input */}
                <div className="w-full md:w-64">
                  <Input
                    label=""
                    placeholder="Search recording or filename…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
            </CardHeader>

            {/* Results Table */}
            <CardBody className="p-0">
              {filteredItems.length === 0 ? (
                <div className="py-12 text-center text-sm text-gray-500">
                  No recordings match the selected filter.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50">
                        <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Diff Status</th>
                        <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Recording ID / File</th>
                        <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Differences</th>
                        <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Base (A)</th>
                        <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Target (B)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filteredItems.map((item) => {
                        const b = item.base_recording
                        const t = item.target_recording
                        return (
                          <tr key={`${item.recording_id}-${item.file_name}`} className="hover:bg-gray-50/70">
                            <td className="px-4 py-3 align-top whitespace-nowrap">
                              <ComparisonDiffTypeBadge diffType={item.diff_type} />
                            </td>
                            <td className="px-4 py-3 align-top">
                              <p className="font-mono text-xs font-medium text-gray-900">{item.recording_id}</p>
                              <p className="text-xs text-gray-600 mt-0.5">{item.file_name}</p>
                            </td>
                            <td className="px-4 py-3 align-top">
                              {item.diff_reasons.length > 0 ? (
                                <ul className="space-y-1">
                                  {item.diff_reasons.map((r, i) => (
                                    <li key={i} className="text-xs text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-block">
                                      {r}
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <span className="text-xs text-gray-400">Identical</span>
                              )}
                            </td>
                            <td className="px-4 py-3 align-top text-xs text-gray-700 space-y-1">
                              {b ? (
                                <>
                                  <div>Size: <span className="tabular-nums font-medium">{formatBytes(b.file_size_bytes)}</span></div>
                                  <div>
                                    SHA-256:{' '}
                                    <span className="font-mono text-gray-500 truncate" title={b.checksum_sha256 ?? ''}>
                                      {b.checksum_sha256 ? `${b.checksum_sha256.slice(0, 10)}…` : '—'}
                                    </span>
                                  </div>
                                  {b.duration_seconds && <div>Duration: {b.duration_seconds}s</div>}
                                  <div><QualityStatusBadge status={b.quality_status} /></div>
                                </>
                              ) : (
                                <span className="text-gray-400 italic">Not in Base</span>
                              )}
                            </td>
                            <td className="px-4 py-3 align-top text-xs text-gray-700 space-y-1">
                              {t ? (
                                <>
                                  <div>Size: <span className="tabular-nums font-medium">{formatBytes(t.file_size_bytes)}</span></div>
                                  <div>
                                    SHA-256:{' '}
                                    <span className="font-mono text-gray-500 truncate" title={t.checksum_sha256 ?? ''}>
                                      {t.checksum_sha256 ? `${t.checksum_sha256.slice(0, 10)}…` : '—'}
                                    </span>
                                  </div>
                                  {t.duration_seconds && <div>Duration: {t.duration_seconds}s</div>}
                                  <div><QualityStatusBadge status={t.quality_status} /></div>
                                </>
                              ) : (
                                <span className="text-gray-400 italic">Removed from Target</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  )
}
