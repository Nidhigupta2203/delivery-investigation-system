import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router'
import { AppLayout } from '../components/layout/AppLayout'
import { DashboardPage }      from '../pages/DashboardPage'
import { OrganizationsPage }  from '../pages/OrganizationsPage'
import { CustomersPage }      from '../pages/CustomersPage'
import { OrdersPage }         from '../pages/OrdersPage'
import { DeliveriesPage }     from '../pages/DeliveriesPage'
import { DeliveryDetailPage } from '../pages/DeliveryDetailPage'

// Root route wraps all routes inside AppLayout
const rootRoute = createRootRoute({
  component: () => (
    <AppLayout>
      <Outlet />
    </AppLayout>
  ),
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
})

const organizationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/organizations',
  component: OrganizationsPage,
})

const customersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/customers',
  component: CustomersPage,
})

const ordersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/orders',
  component: OrdersPage,
})

const deliveriesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/deliveries',
  component: DeliveriesPage,
})

const deliveryDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/deliveries/$deliveryId',
  component: DeliveryDetailPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  organizationsRoute,
  customersRoute,
  ordersRoute,
  deliveriesRoute,
  deliveryDetailRoute,
])

export const router = createRouter({ routeTree })

// Type registration for TanStack Router
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
