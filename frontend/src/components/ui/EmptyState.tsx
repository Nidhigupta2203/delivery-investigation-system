interface Props {
  title: string
  message?: string
}

export function EmptyState({ title, message }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-2">
      <div className="text-4xl text-gray-300">📭</div>
      <h3 className="text-sm font-semibold text-gray-500">{title}</h3>
      {message && <p className="text-xs text-gray-400 max-w-xs">{message}</p>}
    </div>
  )
}
