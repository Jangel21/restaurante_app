from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os

class TicketGenerator:
    """Generador de tickets en formato PDF"""
    
    def __init__(self, output_folder='tickets'):
        self.output_folder = output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Tamaño de ticket térmico (80mm de ancho)
        self.width = 80 * mm
        self.height = 297 * mm  # Alto variable
    
    def generate_ticket(self, order_data):
        """
        Genera un ticket PDF para una orden
        
        Args:
            order_data: Diccionario con datos de la orden
        
        Returns:
            str: Ruta del archivo PDF generado
        """
        filename = f"ticket_{order_data['ticket_number']:04d}.pdf"
        filepath = os.path.join(self.output_folder, filename)
        
        c = canvas.Canvas(filepath, pagesize=(self.width, self.height))
        
        # Posición inicial
        y = self.height - 10*mm
        
        # Encabezado
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.width/2, y, "La Cantina Mexicana")
        y -= 5*mm
        
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width/2, y, "RFC: CME123456ABC")
        y -= 4*mm
        c.drawCentredString(self.width/2, y, "Guadalajara, Jalisco")
        y -= 4*mm
        c.drawCentredString(self.width/2, y, "Tel: (33) 1234-5678")
        y -= 6*mm
        
        # Línea separadora
        c.line(5*mm, y, self.width-5*mm, y)
        y -= 6*mm
        
        # Información del ticket
        c.setFont("Helvetica", 8)
        c.drawString(5*mm, y, f"Ticket: #{order_data['ticket_number']:04d}")
        y -= 4*mm
        c.drawString(5*mm, y, f"Cliente: {order_data['customer_name']}")
        y -= 4*mm
        c.drawString(5*mm, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 6*mm
        
        # Línea separadora
        c.line(5*mm, y, self.width-5*mm, y)
        y -= 6*mm
        
        # Items
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5*mm, y, "Cant.")
        c.drawString(15*mm, y, "Producto")
        c.drawRightString(self.width-5*mm, y, "Total")
        y -= 5*mm
        
        c.setFont("Helvetica", 8)
        for item in order_data['items']:
            # Cantidad y nombre
            c.drawString(5*mm, y, f"{item['quantity']}")
            c.drawString(15*mm, y, item['name'][:25])
            c.drawRightString(self.width-5*mm, y, f"${item['price'] * item['quantity']:.2f}")
            y -= 4*mm
            
            # Precio unitario
            c.setFont("Helvetica", 7)
            c.drawString(15*mm, y, f"${item['price']:.2f} c/u")
            y -= 5*mm
            c.setFont("Helvetica", 8)
        
        y -= 2*mm
        
        # Línea separadora
        c.line(5*mm, y, self.width-5*mm, y)
        y -= 6*mm
        
        # Totales
        c.setFont("Helvetica", 8)
        c.drawString(5*mm, y, "Subtotal:")
        c.drawRightString(self.width-5*mm, y, f"${order_data['subtotal']:.2f}")
        y -= 4*mm
        
        c.drawString(5*mm, y, "IVA (16%):")
        c.drawRightString(self.width-5*mm, y, f"${order_data['iva']:.2f}")
        y -= 6*mm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5*mm, y, "TOTAL:")
        c.drawRightString(self.width-5*mm, y, f"${order_data['total']:.2f}")
        y -= 8*mm
        
        # Línea separadora
        c.line(5*mm, y, self.width-5*mm, y)
        y -= 6*mm
        
        # Pie de página
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(self.width/2, y, "¡Gracias por su preferencia!")
        y -= 4*mm
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width/2, y, "Vuelva pronto 🌮")
        
        c.save()
        return filepath


# Ejemplo de uso
if __name__ == "__main__":
    generator = TicketGenerator()
    
    # Datos de prueba
    test_order = {
        'ticket_number': 1,
        'customer_name': 'Juan Pérez',
        'items': [
            {'name': 'Tacos al Pastor', 'quantity': 3, 'price': 45.00},
            {'name': 'Agua de Horchata', 'quantity': 2, 'price': 25.00}
        ],
        'subtotal': 125.00,
        'iva': 20.00,
        'total': 145.00
    }
    
    filepath = generator.generate_ticket(test_order)
    print(f"Ticket generado: {filepath}")