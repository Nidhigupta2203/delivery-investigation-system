import { useState } from 'react';
import { Button } from '../ui/Button';
import { Card, CardHeader, CardBody } from '../ui/Card';
import { FormField } from '../ui/FormField';
import { LoadingState } from '../ui/Spinner';
import { ErrorMessage } from '../ui/ErrorMessage';
import { deliveriesApi } from '../../api/deliveries';
import type { ManifestCreate, ManifestItemCreate } from '../../types/api';
import { extractErrorMessage } from '../../api/client';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Simple manifest registration form.
 * Allows adding multiple recording entries.
 */
export function ManifestForm({ deliveryId }: { deliveryId: string }) {
  const qc = useQueryClient();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  const [manifestVersion] = useState('1.0'); // fixed as per schema default
  const [sourceLocation, setSourceLocation] = useState('');
  const [targetLocation, setTargetLocation] = useState('');

const createEmptyRecording = (): ManifestItemCreate => ({
  recording_id: "",
  file_name: "",
  file_path: undefined,
  source_key: undefined,
  target_key: undefined,
  file_size_bytes: 0,
  checksum_sha256: "",
  duration_seconds: undefined,
  metadata_json: undefined,
});
  
  const [recordings, setRecordings] = useState<ManifestItemCreate[]>([
    createEmptyRecording(),
  ]);

  const addRecording = () =>
    setRecordings((prev) => [...prev, createEmptyRecording()]);
  const removeRecording = (idx: number) =>
    setRecordings((prev) => prev.filter((_r, i) => i !== idx));

  const handleChange = (
    idx: number,
    field: keyof ManifestItemCreate,
    value: any,
  ) => {
    setRecordings((prev) => {
      const copy = [...prev];
      const record = copy[idx];
      const updated: typeof record = { ...record };
      if (field === 'file_size_bytes') {
        const parsed = Number(value);
        updated[field] = Number.isFinite(parsed) ? parsed : 0;
      } else if (field === 'duration_seconds') {
        updated[field] = value ? Number(value) : undefined;
      } else if (field === 'metadata_json') {
        try {
          updated[field] = value ? JSON.parse(value) : undefined;
        } catch {
          updated[field] = undefined;
        }
      } else {
        updated[field] = value || undefined;
      }
      copy[idx] = updated;
      return copy;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(false);
    const payload: ManifestCreate = {
      manifest_version: manifestVersion,
      source_location: sourceLocation || undefined,
      target_location: targetLocation || undefined,
      recordings,
    };
    try {
      await deliveriesApi.registerManifest(deliveryId, payload);
      setSuccess(true);
      qc.invalidateQueries({ queryKey: ['manifest', deliveryId] });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <h3 className="text-sm font-semibold text-gray-700">Register Manifest</h3>
      </CardHeader>
      <CardBody className="space-y-4">
        {isSubmitting && <LoadingState message="Registering manifest…" />}
        {error && <ErrorMessage message={error} />}
        {success && (
          <div className="p-4 bg-green-100 text-green-800 rounded-md">
            Manifest registered successfully.
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField
            label="Source Location"
            value={sourceLocation}
            onChange={(e) => setSourceLocation(e.target.value)}
            placeholder="optional"
          />
          <FormField
            label="Target Location"
            value={targetLocation}
            onChange={(e) => setTargetLocation(e.target.value)}
            placeholder="optional"
          />
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-gray-600">Recordings</h4>
            {recordings.map((rec, idx) => (
              <div
                key={idx}
                className="grid grid-cols-2 gap-2 p-2 border rounded-md bg-gray-50 relative"
              >
                <button
                  type="button"
                  onClick={() => removeRecording(idx)}
                  className="absolute top-1 right-1 text-xs text-red-500 hover:underline"
                >
                  ✕
                </button>
                <FormField
                  label="Recording ID"
                  value={rec.recording_id ?? ''}
                  onChange={(e) => handleChange(idx, 'recording_id', e.target.value)}
                  required
                />
                <FormField
                  label="File Name"
                  value={rec.file_name ?? ''}
                  onChange={(e) => handleChange(idx, 'file_name', e.target.value)}
                  required
                />
                <FormField
                  label="File Path"
                  value={rec.file_path ?? ''}
                  onChange={(e) => handleChange(idx, 'file_path', e.target.value)}
                />
                <FormField
                  label="Source Key"
                  value={rec.source_key ?? ''}
                  onChange={(e) => handleChange(idx, 'source_key', e.target.value)}
                />
                <FormField
                  label="Target Key"
                  value={rec.target_key ?? ''}
                  onChange={(e) => handleChange(idx, 'target_key', e.target.value)}
                />
                <FormField
                  label="File Size (bytes)"
                  value={rec.file_size_bytes?.toString() ?? ''}
                  onChange={(e) => handleChange(idx, 'file_size_bytes', e.target.value)}
                  type="number"
                />
                <FormField
                  label="SHA‑256 checksum"
                  value={rec.checksum_sha256 ?? ''}
                  onChange={(e) => handleChange(idx, 'checksum_sha256', e.target.value)}
                  required
                />
                <FormField
                  label="Duration (s)"
                  value={rec.duration_seconds?.toString() ?? ''}
                  onChange={(e) => handleChange(idx, 'duration_seconds', e.target.value)}
                  type="number"
                />
                <FormField
                  label="Metadata JSON"
                  value={rec.metadata_json ? JSON.stringify(rec.metadata_json) : ''}
                  onChange={(e) => handleChange(idx, 'metadata_json', e.target.value)}
                  placeholder='{"camera":"front"}'
                />
              </div>
            ))}
            <Button type="button" onClick={addRecording}>+ Add Recording</Button>
          </div>
          <div className="flex justify-end">
            <Button type="submit" loading={isSubmitting}>Register</Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
