import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

interface NavItem {
  to: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { to: '/',                   label: 'Dashboard',     icon: '🏠' },
  { to: '/organizations',      label: 'Organizations', icon: '🏢' },
  { to: '/customers',          label: 'Customers',     icon: '👤' },
  { to: '/orders',             label: 'Orders',        icon: '📋' },
  { to: '/deliveries',         label: 'Deliveries',    icon: '📦' },
  { to: '/deliveries/compare', label: 'Comparison',    icon: '⚖️' },
]

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
        {/* Logo area */}
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-base font-bold text-gray-900 leading-tight">
            📡 Delivery<br />
            <span className="text-blue-600">Investigation</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">Robotics Dataset Platform</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon }) => (
            <Link
              key={to}
              to={to}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
              activeProps={{ className: 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-700' }}
              activeOptions={{ exact: to === '/' }}
            >
              <span className="text-base">{icon}</span>
              {label}
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200">
          <p className="text-xs text-gray-400">v0.1.0 · Development</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
