# Ventana de login segura para la aplicación admin
# Reutiliza tu DBManager existente con credenciales en memoria

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

# Agregar paths para importar tu código existente
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from admin_app.src.services.db_service import SecureDBService

class LoginWindow:
    """
    Ventana de login segura que conecta a la BD usando credenciales del admin
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Browser Control - Admin Login")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')
        
        # Centrar ventana
        self._center_window()
        
        # Variables para credenciales (solo en memoria)
        self.db_service = None
        self.is_connecting = False
        
        # Setup UI
        self.setup_ui()
        
        # Configurar protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        
        # Estilo profesional
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        style.configure('Login.TButton', font=('Arial', 11, 'bold'))
        
        # Frame principal con padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Header
        self._create_header(main_frame)
        
        # Formulario de conexión
        self._create_connection_form(main_frame)
        
        # Botones
        self._create_buttons(main_frame)
        
        # Status bar
        self._create_status_bar(main_frame)
        
    def _create_header(self, parent):
        """Crea el header con título e información"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 30))
        
        # Título principal
        title_label = ttk.Label(
            header_frame, 
            text="🔐 Browser Control Admin", 
            style='Title.TLabel'
        )
        title_label.pack()
        
        # Subtítulo
        subtitle_label = ttk.Label(
            header_frame,
            text="Configure la conexión a su base de datos MySQL",
            style='Subtitle.TLabel'
        )
        subtitle_label.pack(pady=(5, 0))
        
    def _create_connection_form(self, parent):
        """Crea el formulario de conexión"""
        form_frame = ttk.LabelFrame(parent, text="  Configuración de Conexión  ", padding=20)
        form_frame.pack(fill='x', pady=(0, 20))
        
        # Host
        ttk.Label(form_frame, text="Host:").grid(row=0, column=0, sticky='w', pady=5)
        self.host_var = tk.StringVar()  # Campo vacío
        host_entry = ttk.Entry(form_frame, textvariable=self.host_var, width=35, font=('Arial', 10))
        host_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        # Puerto
        ttk.Label(form_frame, text="Puerto:").grid(row=1, column=0, sticky='w', pady=5)
        self.port_var = tk.StringVar()  # Campo vacío
        port_entry = ttk.Entry(form_frame, textvariable=self.port_var, width=35, font=('Arial', 10))
        port_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        # Base de datos
        ttk.Label(form_frame, text="Base de Datos:").grid(row=2, column=0, sticky='w', pady=5)
        self.db_var = tk.StringVar()  # Campo vacío
        db_entry = ttk.Entry(form_frame, textvariable=self.db_var, width=35, font=('Arial', 10))
        db_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        # Usuario
        ttk.Label(form_frame, text="Usuario:").grid(row=3, column=0, sticky='w', pady=5)
        self.user_var = tk.StringVar()
        user_entry = ttk.Entry(form_frame, textvariable=self.user_var, width=35, font=('Arial', 10))
        user_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        # Contraseña
        ttk.Label(form_frame, text="Contraseña:").grid(row=4, column=0, sticky='w', pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            form_frame, 
            textvariable=self.password_var, 
            show="*", 
            width=35, 
            font=('Arial', 10)
        )
        password_entry.grid(row=4, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        # Configurar grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Focus en primer campo (host)
        host_entry.focus_set()
            
        # Bind Enter key
        password_entry.bind('<Return>', lambda event: self.connect_to_database())
        
    def _create_buttons(self, parent):
        """Crea los botones de acción"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(0, 15))
        
        # Frame para centrar botones
        center_frame = ttk.Frame(button_frame)
        center_frame.pack()
        
        # Botón conectar
        self.connect_btn = ttk.Button(
            center_frame, 
            text="🔌 Conectar", 
            command=self.connect_to_database,
            style='Login.TButton',
            width=15
        )
        self.connect_btn.pack(side='left', padx=(0, 10))
        
        # Botón cancelar
        cancel_btn = ttk.Button(
            center_frame, 
            text="❌ Salir", 
            command=self.on_closing,
            width=15
        )
        cancel_btn.pack(side='left')
        
    def _create_status_bar(self, parent):
        """Crea la barra de estado"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x')
        
        self.status_var = tk.StringVar(value="💡 Complete todos los campos de conexión para continuar")
        self.status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            font=('Arial', 9),
            foreground='#3498db'
        )
        self.status_label.pack()
        
        # Progress bar (oculta inicialmente)
        self.progress = ttk.Progressbar(
            status_frame, 
            mode='indeterminate', 
            length=300
        )
        
    def connect_to_database(self):
        """Conecta a la base de datos con validación segura"""
        
        if self.is_connecting:
            return
            
        # Validar campos obligatorios
        required_fields = [
            (self.host_var.get(), "Host"),
            (self.user_var.get(), "Usuario"),
            (self.password_var.get(), "Contraseña"),
            (self.db_var.get(), "Base de Datos")
        ]
        
        for value, field_name in required_fields:
            if not value.strip():
                messagebox.showerror("Campo Requerido", f"El campo '{field_name}' es obligatorio")
                return
        
        # Validar puerto
        try:
            port = int(self.port_var.get())
            if not (1 <= port <= 65535):
                raise ValueError()
        except ValueError:
            messagebox.showerror("Puerto Inválido", "El puerto debe ser un número entre 1 y 65535")
            return
        
        # Iniciar proceso de conexión
        self._start_connection_process()
        
        # Ejecutar conexión en hilo separado
        connection_thread = threading.Thread(target=self._connect_thread, daemon=True)
        connection_thread.start()
        
    def _start_connection_process(self):
        """Inicia el proceso visual de conexión"""
        self.is_connecting = True
        self.connect_btn.config(state='disabled', text="🔄 Conectando...")
        self.status_var.set("🔄 Estableciendo conexión con la base de datos...")
        self.status_label.config(foreground='#f39c12')
        
        # Mostrar progress bar
        self.progress.pack(pady=(10, 0))
        self.progress.start(10)
        
    def _connect_thread(self):
        """Maneja la conexión en hilo separado para no bloquear UI"""
        try:
            # Crear servicio de BD
            db_service = SecureDBService()
            
            # Intentar conexión
            success, error = db_service.connect(
                host=self.host_var.get().strip(),
                port=int(self.port_var.get().strip()),
                user=self.user_var.get().strip(),
                password=self.password_var.get(),
                database=self.db_var.get().strip()
            )
            
            # Actualizar UI en hilo principal
            self.root.after(0, self._handle_connection_result, success, error, db_service)
            
        except Exception as e:
            self.root.after(0, self._handle_connection_result, False, f"Error inesperado: {str(e)}", None)
    
    def _handle_connection_result(self, success: bool, error: str, db_service):
        """Maneja el resultado de la conexión"""
        
        # Detener progress bar
        self.progress.stop()
        self.progress.pack_forget()
        
        # Rehabilitar botón
        self.connect_btn.config(state='normal', text="🔌 Conectar")
        self.is_connecting = False
        
        if success:
            self.status_var.set("✅ Conexión exitosa - Abriendo panel de administración...")
            self.status_label.config(foreground='#27ae60')
            self.db_service = db_service
            
            # Abrir panel principal después de un breve delay
            self.root.after(1500, self.open_main_panel)
            
        else:
            self.status_var.set("❌ Error de conexión")
            self.status_label.config(foreground='#e74c3c')
            
            # Mostrar error detallado
            messagebox.showerror(
                "Error de Conexión", 
                f"No se pudo conectar a la base de datos:\n\n{error}\n\nVerifique sus credenciales e intente nuevamente."
            )
    
    def open_main_panel(self):
        """Abre el panel principal de administración"""
        try:
            from admin_app.src.ui.main_window import MainWindow
            
            # Crear ventana principal con la conexión establecida
            main_window = MainWindow(self.db_service)
            
            # Ocultar ventana de login
            self.root.withdraw()
            
            # Ejecutar panel principal
            main_window.run()
            
            # Cerrar login cuando se cierre el panel principal
            self.root.quit()
            
        except ImportError as e:
            messagebox.showerror(
                "Error", 
                f"No se pudo cargar el panel principal:\n{e}\n\nAsegúrese de que todos los archivos estén presentes."
            )
            
    def on_closing(self):
        """Maneja el cierre de la ventana"""
        if self.is_connecting:
            if messagebox.askokcancel("Cerrando", "Hay una conexión en progreso. ¿Desea cancelar?"):
                self.root.quit()
        else:
            self.root.quit()
    
    def run(self):
        """Ejecuta la ventana de login"""
        self.root.mainloop()

if __name__ == "__main__":
    # Test independiente
    app = LoginWindow()
    app.run()