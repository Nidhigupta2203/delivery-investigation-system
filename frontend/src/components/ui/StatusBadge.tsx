import type {
  ComparisonDiffType,
  DeliveryStatus,
  FileTransferStatus,
  OrderStatus,
  QualityStatus,
  TransferJobStatus,
} from '../../types/api'

type BadgeVariant = 'gray' | 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'indigo'

const variantClasses: Record<BadgeVariant, string> = {
  gray:   'bg-gray-100 text-gray-700',
  blue:   'bg-blue-100 text-blue-700',
  green:  'bg-green-100 text-green-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  red:    'bg-red-100 text-red-700',
  purple: 'bg-purple-100 text-purple-700',
  indigo: 'bg-indigo-100 text-indigo-700',
}

interface BadgeProps {
  label: string
  variant: BadgeVariant
}

function Badge({ label, variant }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]}`}>
      {label}
    </span>
  )
}

// ── Specialized badges ────────────────────────────────────────────────────────

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const map: Record<OrderStatus, BadgeVariant> = {
    PENDING:     'gray',
    IN_PROGRESS: 'blue',
    FULFILLED:   'green',
    CANCELLED:   'red',
  }
  return <Badge label={status.replace('_', ' ')} variant={map[status]} />
}

export function DeliveryStatusBadge({ status }: { status: DeliveryStatus }) {
  const map: Record<DeliveryStatus, BadgeVariant> = {
    PLANNED:      'gray',
    TRANSFERRING: 'blue',
    TRANSFERRED:  'indigo',
    ACCEPTED:     'green',
    REJECTED:     'red',
  }
  return <Badge label={status} variant={map[status]} />
}

export function TransferJobStatusBadge({ status }: { status: TransferJobStatus }) {
  const map: Record<TransferJobStatus, BadgeVariant> = {
    PENDING:     'gray',
    IN_PROGRESS: 'blue',
    COMPLETED:   'green',
    FAILED:      'red',
    CANCELLED:   'yellow',
  }
  return <Badge label={status.replace('_', ' ')} variant={map[status]} />
}

export function FileTransferStatusBadge({ status }: { status: FileTransferStatus }) {
  const map: Record<FileTransferStatus, BadgeVariant> = {
    PENDING:      'gray',
    TRANSFERRING: 'blue',
    COMPLETED:    'green',
    FAILED:       'red',
    SKIPPED:      'yellow',
  }
  return <Badge label={status} variant={map[status]} />
}

export function QualityStatusBadge({ status }: { status: QualityStatus }) {
  const map: Record<QualityStatus, BadgeVariant> = {
    PENDING_REVIEW: 'gray',
    PASSED:         'green',
    WARNING:        'yellow',
    FAILED:         'red',
  }
  return <Badge label={status.replace('_', ' ')} variant={map[status]} />
}

export function ComparisonDiffTypeBadge({ diffType }: { diffType: ComparisonDiffType }) {
  const map: Record<ComparisonDiffType, BadgeVariant> = {
    ADDED:     'green',
    REMOVED:   'red',
    CHANGED:   'yellow',
    UNCHANGED: 'gray',
  }
  return <Badge label={diffType} variant={map[diffType]} />
}
