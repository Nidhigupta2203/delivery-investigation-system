interface Props {
  message: string
}

export function ErrorMessage({ message }: Props) {
  return (
    <div className="rounded-md bg-red-50 border border-red-200 p-4">
      <div className="flex items-start gap-3">
        <span className="text-red-500 text-lg leading-none">⚠</span>
        <p className="text-sm text-red-700">{message}</p>
      </div>
    </div>
  )
}
