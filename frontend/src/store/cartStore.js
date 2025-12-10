import { create } from 'zustand'

export const useCartStore = create((set, get) => ({
  items: [],
  orderId: null,
  orderType: 'local',
  customerName: '',
  deliveryPhone: '',
  deliveryAddress: '',

  addItem: (menuItem, quantity = 1, notes = '') => {
    const currentItems = get().items
    const existingIndex = currentItems.findIndex(
      item => item.menu_item.id === menuItem.id && item.notes === notes
    )

    if (existingIndex !== -1) {
      // Actualizar cantidad
      const newItems = [...currentItems]
      newItems[existingIndex].quantity += quantity
      set({ items: newItems })
    } else {
      // Agregar nuevo item
      set({
        items: [
          ...currentItems,
          {
            menu_item: menuItem,
            quantity,
            notes,
            unit_price: menuItem.price,
            subtotal: menuItem.price * quantity,
          },
        ],
      })
    }
  },

  updateItemQuantity: (index, quantity) => {
    const items = get().items
    if (quantity <= 0) {
      set({ items: items.filter((_, i) => i !== index) })
    } else {
      const newItems = [...items]
      newItems[index].quantity = quantity
      newItems[index].subtotal = newItems[index].unit_price * quantity
      set({ items: newItems })
    }
  },

  removeItem: (index) => {
    set({ items: get().items.filter((_, i) => i !== index) })
  },

  updateItemNotes: (index, notes) => {
    const newItems = [...get().items]
    newItems[index].notes = notes
    set({ items: newItems })
  },

  setOrderInfo: (info) => set(info),

  clearCart: () =>
    set({
      items: [],
      orderId: null,
      orderType: 'local',
      customerName: '',
      deliveryPhone: '',
      deliveryAddress: '',
    }),

  getTotal: () => {
    const items = get().items
    const subtotal = items.reduce((sum, item) => sum + item.subtotal, 0)
    const iva = subtotal * 0.16
    return {
      subtotal,
      iva,
      total: subtotal + iva,
    }
  },
}))