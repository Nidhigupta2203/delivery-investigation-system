// ---------------------------------------------------------------------------
// API Types — mirrors the FastAPI Pydantic schemas exactly
// ---------------------------------------------------------------------------

// ── Shared ──────────────────────────────────────────────────────────────────

export type UUID = string

// ── Organizations ───────────────────────────────────────────────────────────

export interface Organization {
  id: UUID
  name: string
  code: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface OrganizationCreate {
  name: string
  code: string
  is_active?: boolean
}

export interface OrganizationUpdate {
  name?: string
  code?: string
  is_active?: boolean
}

// ── Customers ────────────────────────────────────────────────────────────────

export interface Customer {
  id: UUID
  organization_id: UUID
  name: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CustomerCreate {
  organization_id: UUID
  name: string
  email: string
  is_active?: boolean
}

// ── Orders ───────────────────────────────────────────────────────────────────

export type OrderStatus = 'PENDING' | 'IN_PROGRESS' | 'FULFILLED' | 'CANCELLED'

export interface Order {
  id: UUID
  customer_id: UUID
  order_number: string
  requested_recordings_count: number
  description: string | null
  status: OrderStatus
  created_at: string
  updated_at: string
}

export interface OrderCreate {
  customer_id: UUID
  order_number: string
  requested_recordings_count?: number
  description?: string
}

export interface OrderStatusUpdate {
  status: OrderStatus
}

// ── Deliveries ───────────────────────────────────────────────────────────────

export type DeliveryStatus =
  | 'PLANNED'
  | 'TRANSFERRING'
  | 'TRANSFERRED'
  | 'ACCEPTED'
  | 'REJECTED'

export interface Delivery {
  id: UUID
  order_id: UUID
  delivery_number: string
  status: DeliveryStatus
  source_location: string | null
  target_location: string | null
  rejection_reason: string | null
  decision_notes: string | null
  accepted_at: string | null
  rejected_at: string | null
  created_at: string
  updated_at: string
}

export interface DeliveryCreate {
  order_id: UUID
  delivery_number: string
  source_location?: string
  target_location?: string
}

export interface DeliveryStatusUpdate {
  status: DeliveryStatus
  rejection_reason?: string
  decision_notes?: string
}

// ── Manifest ──────────────────────────────────────────────────────────────────

export type QualityStatus = 'PENDING_REVIEW' | 'PASSED' | 'WARNING' | 'FAILED'

export interface ManifestRecording {
  id: UUID
  delivery_id: UUID
  recording_id: string
  file_name: string
  file_path: string
  file_size_bytes: number
  checksum_sha256: string | null
  duration_seconds: number | null
  quality_status: QualityStatus
  metadata_json: Record<string, unknown> | null
  created_at: string
}

export interface ManifestResponse {
  delivery_id: UUID
  delivery_number: string
  source_location: string | null
  target_location: string | null
  total_recordings: number
  total_bytes: number
  recordings: ManifestRecording[]
}

export interface ManifestItemCreate {
  recording_id: string
  file_name: string
  file_path?: string
  source_key?: string
  target_key?: string
  file_size_bytes?: number
  checksum_sha256: string
  duration_seconds?: number
  metadata_json?: Record<string, unknown>
}

export interface ManifestCreate {
  manifest_version?: string
  source_location?: string
  target_location?: string
  recordings: ManifestItemCreate[]
}

// ── Transfers ──────────────────────────────────────────────────────────────────

export type TransferJobStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'

export type FileTransferStatus =
  | 'PENDING'
  | 'TRANSFERRING'
  | 'COMPLETED'
  | 'FAILED'
  | 'SKIPPED'

export interface FileTransfer {
  id: UUID
  recording_id: UUID
  source_bucket: string
  source_key: string
  target_bucket: string
  target_key: string
  file_size_bytes: number
  expected_checksum: string
  actual_checksum: string | null
  status: FileTransferStatus
  error_message: string | null
  transferred_at: string | null
}

export interface TransferJob {
  id: UUID
  delivery_id: UUID
  status: TransferJobStatus
  total_files: number
  transferred_files: number
  total_bytes: number
  transferred_bytes: number
  retry_count: number
  progress_percentage: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  file_transfers: FileTransfer[]
}

// ── API error ──────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string
}
