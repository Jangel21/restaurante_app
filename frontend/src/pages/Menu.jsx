import { useEffect, useState } from 'react'
import { menuAPI, ordersAPI } from '../services/api'
import { useCartStore } from '../store/cartStore'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import {
  Plus,
  Minus,
  ShoppingCart,
  Trash2,
  Save,
  X,
} from 'lucide-react'

function Menu() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const {
    items: cartItems,
    addItem,
    updateItemQuantity,
    removeItem,
    updateItemNotes,
    clearCart,
    getTotal,
    orderType,
    customerName,
    deliveryPhone,
    deliveryAddress,
    setOrderInfo,
  } = useCartStore()

  const [menuItems, setMenuItems] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('Todos')
  const [loading, setLoading] = useState(true)
  const [showCartModal, setShowCartModal] = useState(false)
  const [showOrderInfoModal, setShowOrderInfoModal] = useState(false)
  const [creating, setCreating] = useState(false)

  // Estados del formulario
  const [formData, setFormData] = useState({
    orderType: orderType || 'local',
    customerName: customerName || '',
    deliveryPhone: deliveryPhone || '',
    deliveryAddress: deliveryAddress || '',
  })

  useEffect(() => {
    loadCategories()
    loadMenu()
  }, [selectedCategory])

  const loadCategories = async () => {
    try {
      const response = await menuAPI.getCategories()
      setCategories(['Todos', ...response.data])
    } catch (error) {
      console.error('Error loading categories:', error)
    }
  }

  const loadMenu = async () => {
    setLoading(true)
    try {
      const response = await menuAPI.getAll(
        selectedCategory === 'Todos' ? null : selectedCategory
      )
      setMenuItems(response.data)
    } catch (error) {
      console.error('Error loading menu:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = (item) => {
    addItem(item, 1)
  }

  const handleCreateOrder = () => {
    if (cartItems.length === 0) {
      alert('Agrega productos al carrito')
      return
    }
    setShowOrderInfoModal(true)
  }

  const handleSubmitOrder = async () => {
    // Validar según tipo de orden
    if (!formData.customerName.trim()) {
      alert('Ingresa el nombre del cliente')
      return
    }

    if (formData.orderType === 'delivery') {
      if (!formData.deliveryPhone.trim()) {
        alert('Ingresa el teléfono para entrega a domicilio')
        return
      }
      if (!formData.deliveryAddress.trim()) {
        alert('Ingresa la dirección para entrega a domicilio')
        return
      }
    }

    setCreating(true)
    try {
      // Guardar info de la orden en el store
      setOrderInfo({
        orderType: formData.orderType,
        customerName: formData.customerName,
        deliveryPhone: formData.deliveryPhone,
        deliveryAddress: formData.deliveryAddress,
      })

      const orderData = {
        customer_name: formData.customerName,
        order_type: formData.orderType,
        delivery_phone:
          formData.orderType === 'delivery' ? formData.deliveryPhone : null,
        delivery_address:
          formData.orderType === 'delivery' ? formData.deliveryAddress : null,
        items: cartItems.map((item) => ({
          id: item.menu_item.id,
          quantity: item.quantity,
          notes: item.notes || null,
        })),
      }

      const response = await ordersAPI.create(orderData)
      alert(
        `Orden #${response.data.ticket_number} creada exitosamente`
      )
      clearCart()
      setShowOrderInfoModal(false)
      setShowCartModal(false)
      navigate('/open-orders')
    } catch (error) {
      alert(
        error.response?.data?.error || 'Error al crear la orden'
      )
    } finally {
      setCreating(false)
    }
  }

  const totals = getTotal()

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Menú</h1>
          <p className="text-gray-500">Selecciona productos para la orden</p>
        </div>

        {/* Cart Button */}
        <button
          onClick={() => setShowCartModal(true)}
          className="btn btn-primary relative"
        >
          <ShoppingCart className="w-5 h-5 mr-2" />
          Carrito
          {cartItems.length > 0 && (
            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
              {cartItems.length}
            </span>
          )}
        </button>
      </div>

      {/* Categories */}
      <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
              selectedCategory === category
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Menu Items Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-gray-200 rounded mb-4"></div>
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {menuItems.map((item) => (
            <div
              key={item.id}
              className="card hover:shadow-lg transition-shadow"
            >
              {/* Imagen placeholder */}
              <div className="h-32 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg mb-4 flex items-center justify-center">
                <span className="text-4xl">🍽️</span>
              </div>

              <h3 className="font-semibold text-lg mb-1">{item.name}</h3>
              <p className="text-gray-500 text-sm mb-3 line-clamp-2">
                {item.description || 'Delicioso platillo mexicano'}
              </p>

              <div className="flex justify-between items-center">
                <span className="text-2xl font-bold text-primary-600">
                  ${item.price.toFixed(2)}
                </span>
                <button
                  onClick={() => handleAddToCart(item)}
                  className="btn btn-primary"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Agregar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cart Modal */}
      {showCartModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-2xl font-bold">Carrito de Compras</h2>
              <button
                onClick={() => setShowCartModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {cartItems.length === 0 ? (
                <div className="text-center py-12">
                  <ShoppingCart className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">El carrito está vacío</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {cartItems.map((item, index) => (
                    <div
                      key={index}
                      className="border rounded-lg p-4 space-y-3"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-semibold">
                            {item.menu_item.name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            ${item.unit_price.toFixed(2)} c/u
                          </p>
                        </div>
                        <button
                          onClick={() => removeItem(index)}
                          className="text-red-600 hover:bg-red-50 p-2 rounded-lg"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() =>
                            updateItemQuantity(index, item.quantity - 1)
                          }
                          className="btn btn-secondary p-2"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <span className="font-semibold w-12 text-center">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() =>
                            updateItemQuantity(index, item.quantity + 1)
                          }
                          className="btn btn-secondary p-2"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                        <span className="ml-auto font-bold text-lg">
                          ${item.subtotal.toFixed(2)}
                        </span>
                      </div>

                      {/* Notes */}
                      <input
                        type="text"
                        placeholder="Notas especiales (ej: sin cebolla)"
                        value={item.notes || ''}
                        onChange={(e) =>
                          updateItemNotes(index, e.target.value)
                        }
                        className="input text-sm"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Totals and Actions */}
            {cartItems.length > 0 && (
              <div className="border-t p-6 space-y-4 bg-gray-50">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Subtotal:</span>
                    <span className="font-medium">
                      ${totals.subtotal.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">IVA (16%):</span>
                    <span className="font-medium">
                      ${totals.iva.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xl font-bold border-t pt-2">
                    <span>Total:</span>
                    <span className="text-primary-600">
                      ${totals.total.toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      if (
                        confirm('¿Vaciar el carrito?')
                      ) {
                        clearCart()
                        setShowCartModal(false)
                      }
                    }}
                    className="btn btn-secondary flex-1"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Vaciar
                  </button>
                  <button
                    onClick={handleCreateOrder}
                    className="btn btn-primary flex-1"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Crear Orden
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Order Info Modal */}
      {showOrderInfoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 border-b">
              <h2 className="text-2xl font-bold">Información de la Orden</h2>
            </div>

            <div className="p-6 space-y-4">
              {/* Order Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Orden
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'local', label: 'Local' },
                    { value: 'takeout', label: 'Para Llevar' },
                    { value: 'delivery', label: 'Domicilio' },
                  ].map((type) => (
                    <button
                      key={type.value}
                      onClick={() =>
                        setFormData({ ...formData, orderType: type.value })
                      }
                      className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                        formData.orderType === type.value
                          ? 'border-primary-600 bg-primary-50 text-primary-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Customer Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {formData.orderType === 'local'
                    ? 'Mesa / Cliente'
                    : 'Nombre del Cliente'}
                  <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.customerName}
                  onChange={(e) =>
                    setFormData({ ...formData, customerName: e.target.value })
                  }
                  className="input"
                  placeholder={
                    formData.orderType === 'local'
                      ? 'Ej: Mesa 5'
                      : 'Nombre completo'
                  }
                  required
                />
              </div>

              {/* Delivery Fields */}
              {formData.orderType === 'delivery' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Teléfono <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="tel"
                      value={formData.deliveryPhone}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          deliveryPhone: e.target.value,
                        })
                      }
                      className="input"
                      placeholder="33-1234-5678"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Dirección <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={formData.deliveryAddress}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          deliveryAddress: e.target.value,
                        })
                      }
                      className="input"
                      rows="3"
                      placeholder="Calle, número, colonia..."
                      required
                    />
                  </div>
                </>
              )}
            </div>

            <div className="p-6 border-t flex gap-3">
              <button
                onClick={() => setShowOrderInfoModal(false)}
                className="btn btn-secondary flex-1"
                disabled={creating}
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmitOrder}
                className="btn btn-primary flex-1"
                disabled={creating}
              >
                {creating ? 'Creando...' : 'Crear Orden'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Menu