import { useEffect, useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { ordersAPI, reportsAPI } from '../services/api'
import { Link } from 'react-router-dom'
import {
  DollarSign,
  ShoppingCart,
  TrendingUp,
  FileText,
} from 'lucide-react'

function Dashboard() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState({
    openOrders: 0,
    todaySales: 0,
    todayOrders: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [openOrdersRes, dailyReportRes] = await Promise.all([
        ordersAPI.getOpen(),
        user.role === 'admin'
          ? reportsAPI.daily()
          : Promise.resolve({ data: { total_sales: 0, total_orders: 0 } }),
      ])

      setStats({
        openOrders: openOrdersRes.data.length,
        todaySales: dailyReportRes.data.total_sales || 0,
        todayOrders: dailyReportRes.data.total_orders || 0,
      })
    } catch (error) {
      console.error('Error loading stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const cards = [
    {
      title: 'Tickets Abiertos',
      value: stats.openOrders,
      icon: FileText,
      color: 'bg-blue-500',
      link: '/open-orders',
    },
    ...(user.role === 'admin'
      ? [
          {
            title: 'Ventas del Día',
            value: `$${stats.todaySales.toFixed(2)}`,
            icon: DollarSign,
            color: 'bg-green-500',
            link: '/reports',
          },
          {
            title: 'Órdenes del Día',
            value: stats.todayOrders,
            icon: ShoppingCart,
            color: 'bg-purple-500',
            link: '/orders',
          },
        ]
      : []),
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Bienvenido, {user?.full_name}
        </h1>
        <p className="text-gray-500 mt-1">
          {user?.role === 'admin' && 'Panel de administración'}
          {user?.role === 'cashier' && 'Panel de caja'}
          {user?.role === 'waiter' && 'Panel de mesero'}
        </p>
      </div>

      {/* Stats Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-24 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {cards.map((card, index) => {
            const Icon = card.icon
            return (
              <Link
                key={index}
                to={card.link}
                className="card hover:shadow-lg transition-shadow cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {card.value}
                    </p>
                  </div>
                  <div className={`${card.color} p-3 rounded-lg`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/menu"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-center"
          >
            <ShoppingCart className="w-8 h-8 mx-auto mb-2 text-primary-600" />
            <p className="font-medium">Nueva Orden</p>
          </Link>

          <Link
            to="/open-orders"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-center"
          >
            <FileText className="w-8 h-8 mx-auto mb-2 text-primary-600" />
            <p className="font-medium">Ver Tickets Abiertos</p>
          </Link>

          <Link
            to="/orders"
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-center"
          >
            <TrendingUp className="w-8 h-8 mx-auto mb-2 text-primary-600" />
            <p className="font-medium">Historial</p>
          </Link>

          {user.role === 'admin' && (
            <Link
              to="/reports"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-center"
            >
              <DollarSign className="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <p className="font-medium">Reportes</p>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard