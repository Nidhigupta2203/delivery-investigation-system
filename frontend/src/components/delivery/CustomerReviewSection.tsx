import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deliveriesApi } from '../../api/deliveries'
import { Card, CardBody, CardHeader } from '../ui/Card'
import { Button } from '../ui/Button'
import { Textarea } from '../ui/FormField'
import { ErrorMessage } from '../ui/ErrorMessage'
import { DeliveryStatusBadge } from '../ui/StatusBadge'
import { extractErrorMessage } from '../../api/client'
import type { Delivery, DeliveryStatus } from '../../types/api'

interface CustomerReviewSectionProps {
  delivery: Delivery
}

export function CustomerReviewSection({ delivery }: CustomerReviewSectionProps) {
  const qc = useQueryClient()
  const [activeAction, setActiveAction] = useState<'ACCEPT' | 'REJECT' | null>(null)
  const [rejectionReason, setRejectionReason] = useState(delivery.rejection_reason ?? '')
  const [decisionNotes, setDecisionNotes] = useState(delivery.decision_notes ?? '')
  const [validationError, setValidationError] = useState<string | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (payload: { status: DeliveryStatus; rejection_reason?: string; decision_notes?: string }) =>
      deliveriesApi.updateStatus(delivery.id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['delivery', delivery.id] })
      qc.invalidateQueries({ queryKey: ['deliveries'] })
      setActiveAction(null)
      setValidationError(null)
      setApiError(null)
    },
    onError: (err) => {
      setApiError(extractErrorMessage(err))
    },
  })

  const openActionForm = (action: 'ACCEPT' | 'REJECT') => {
    setActiveAction(action)
    setValidationError(null)
    setApiError(null)
    if (action === 'ACCEPT') {
      setRejectionReason('')
      setDecisionNotes(delivery.decision_notes ?? '')
    } else {
      setRejectionReason(delivery.rejection_reason ?? '')
      setDecisionNotes(delivery.decision_notes ?? '')
    }
  }

  const cancelAction = () => {
    setActiveAction(null)
    setValidationError(null)
    setApiError(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError(null)
    setApiError(null)

    if (activeAction === 'REJECT') {
      const trimmedReason = rejectionReason.trim()
      if (!trimmedReason) {
        setValidationError('Rejection reason is mandatory and cannot be empty.')
        return
      }
      mutation.mutate({
        status: 'REJECTED',
        rejection_reason: trimmedReason,
        decision_notes: decisionNotes.trim() || undefined,
      })
    } else if (activeAction === 'ACCEPT') {
      mutation.mutate({
        status: 'ACCEPTED',
        decision_notes: decisionNotes.trim() || undefined,
      })
    }
  }

  const isAccepted = delivery.status === 'ACCEPTED'
  const isRejected = delivery.status === 'REJECTED'

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-base">⚖️</span>
            <h3 className="text-sm font-semibold text-gray-800">Customer Review & Decision</h3>
          </div>
          <DeliveryStatusBadge status={delivery.status} />
        </div>
      </CardHeader>
      <CardBody className="space-y-4">
        {/* Status Banner */}
        {isAccepted && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <div className="flex items-start gap-3">
              <span className="text-xl">✅</span>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-green-900">Delivery Accepted</p>
                <p className="text-xs text-green-700">
                  Accepted on{' '}
                  {delivery.accepted_at
                    ? new Date(delivery.accepted_at).toLocaleString()
                    : 'record'}
                  . All dataset deliverables have been verified and approved.
                </p>
                {delivery.decision_notes && (
                  <div className="mt-2 text-xs text-green-800 bg-white/70 rounded p-2 border border-green-100">
                    <span className="font-semibold">Review Notes: </span>
                    {delivery.decision_notes}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {isRejected && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="flex items-start gap-3">
              <span className="text-xl">❌</span>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-red-900">Delivery Rejected</p>
                <p className="text-xs text-red-700">
                  Rejected on{' '}
                  {delivery.rejected_at
                    ? new Date(delivery.rejected_at).toLocaleString()
                    : 'record'}
                  .
                </p>
                <div className="mt-2 text-xs text-red-900 bg-white/80 rounded p-2.5 border border-red-200">
                  <span className="font-semibold block mb-0.5">Rejection Reason:</span>
                  <p className="whitespace-pre-wrap">{delivery.rejection_reason}</p>
                </div>
                {delivery.decision_notes && (
                  <div className="mt-2 text-xs text-gray-700 bg-white/60 rounded p-2 border border-red-100">
                    <span className="font-semibold">Investigation Notes: </span>
                    {delivery.decision_notes}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {!isAccepted && !isRejected && (
          <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-4">
            <p className="text-xs text-blue-900 leading-relaxed">
              Verify recording counts, checksum integrity, and sensor calibration metrics below.
              Acceptance approves the delivery for dataset ingestion, while rejection halts processing and requires an audit reason.
            </p>
          </div>
        )}

        {/* Action Form or Buttons */}
        {activeAction ? (
          <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 bg-gray-50/50 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-gray-200">
              <h4 className="text-sm font-semibold text-gray-800">
                {activeAction === 'ACCEPT' ? 'Accept Delivery' : 'Reject Delivery'}
              </h4>
              <span className="text-xs text-gray-500 font-mono">{delivery.delivery_number}</span>
            </div>

            {validationError && <ErrorMessage message={validationError} />}
            {apiError && <ErrorMessage message={apiError} />}

            {activeAction === 'REJECT' && (
              <Textarea
                label="Rejection Reason *"
                placeholder="Describe data anomalies, missing timestamps, checksum mismatches, or camera sensor defects..."
                rows={3}
                value={rejectionReason}
                onChange={(e) => {
                  setRejectionReason(e.target.value)
                  if (validationError) setValidationError(null)
                }}
                required
              />
            )}

            <Textarea
              label="Decision Notes (optional)"
              placeholder="Add internal notes, reviewer comments, or follow-up action items..."
              rows={2}
              value={decisionNotes}
              onChange={(e) => setDecisionNotes(e.target.value)}
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" size="sm" onClick={cancelAction} disabled={mutation.isPending}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant={activeAction === 'ACCEPT' ? 'primary' : 'danger'}
                size="sm"
                loading={mutation.isPending}
              >
                {activeAction === 'ACCEPT' ? 'Confirm Acceptance' : 'Confirm Rejection'}
              </Button>
            </div>
          </form>
        ) : (
          <div className="flex flex-wrap items-center gap-3 pt-1">
            {!isAccepted && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => openActionForm('ACCEPT')}
              >
                ✓ Accept Delivery
              </Button>
            )}
            {!isRejected && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => openActionForm('REJECT')}
              >
                ✕ Reject Delivery
              </Button>
            )}
            {(isAccepted || isRejected) && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => openActionForm(isAccepted ? 'REJECT' : 'ACCEPT')}
              >
                🔄 Change Review Decision
              </Button>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  )
}
