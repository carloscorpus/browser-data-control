# Ventana principal de administración
# Panel completo para gestionar usuarios y generar EXE

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
import os
from datetime import datetime, timedelta

# Agregar paths para importar código existente
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

class MainWindow:
    """
    Panel principal de administración para Browser Control
    """
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.root = tk.Tk()
        self.root.title("Browser Control - Panel de Administración")
        self.root.geometry("1000x700")
        self.root.configure(bg='#ecf0f1')
        
        # Variables de estado
        self.practitioners_data = []
        self.selected_practitioner = None
        self.selected_end_date = None  # Fecha de fin de convenio del usuario seleccionado
        self.validated_exe_user = None  # Usuario validado para generación EXE
        self.last_full_sync_ts = None   # Timestamp del último full refresh
        self.max_seen_id = 0            # Máximo practitioner_id visto para altas incrementales
        self.showing_inactives = False  # Estado actual del filtro de inactivos
        
        # Setup UI
        self.setup_ui()
        
        # Cargar datos iniciales
        self.refresh_practitioners()
        
        # Configurar protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Configura la interfaz principal"""
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar estilos personalizados
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        style.configure('Subheader.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        
        # Header principal
        self._create_header()
        
        # Frame principal con pestañas
        self._create_main_content()
        
        # Status bar
        self._create_status_bar()
        
    def _create_header(self):
        """Crea el header principal"""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=(20, 0))
        
        # Título
        title_label = ttk.Label(
            header_frame,
            text="🛠️ Browser Control - Panel de Administración",
            style='Header.TLabel'
        )
        title_label.pack(side='left')
        
        # Info de conexión
        connection_info = f"📊 Conectado a: {self.db_service.connection_params.get('database', 'N/A')}"
        info_label = ttk.Label(
            header_frame,
            text=connection_info,
            font=('Arial', 9),
            foreground='#27ae60'
        )
        info_label.pack(side='right')
        
    def _create_main_content(self):
        """Crea el contenido principal con pestañas"""
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Pestaña 1: Gestión de Usuarios
        self._create_users_tab()
        
        # Pestaña 2: Generación de EXE
        self._create_exe_tab()
        
        # Pestaña 3: Configuración
        self._create_config_tab()
        
    def _create_users_tab(self):
        """Crea la pestaña de gestión de usuarios"""
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="👥 Gestión de Usuarios")
        
        # Panel izquierdo: Lista de usuarios
        left_panel = ttk.LabelFrame(users_frame, text="  Lista de Usuarios  ", padding=10)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Toolbar de usuarios
        toolbar_frame = ttk.Frame(left_panel)
        toolbar_frame.pack(fill='x', pady=(0, 10))
        
        refresh_btn = ttk.Button(
            toolbar_frame,
            text="🔄 Actualizar (inteligente)",
            command=self.smart_refresh
        )
        refresh_btn.pack(side='left', padx=(0, 5))
        
        refresh_one_btn = ttk.Button(
            toolbar_frame,
            text="🔁 Actualizar seleccionado",
            command=self.refresh_selected_practitioner
        )
        refresh_one_btn.pack(side='left', padx=(0, 5))

        # Botón incremental se sustituye por el inteligente; si quieres, podemos ocultarlo

        self.toggle_inactive_btn = ttk.Button(
            toolbar_frame,
            text="⚠️ Mostrar Inactivos",
            command=self.toggle_inactives
        )
        self.toggle_inactive_btn.pack(side='left')
        
        # Treeview para usuarios
        columns = ('ID', 'General ID', 'Estado', 'Fecha Inicio', 'Fecha Fin', 'Observación')
        self.users_tree = ttk.Treeview(left_panel, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.users_tree.heading('ID', text='ID')
        self.users_tree.heading('General ID', text='General ID')
        self.users_tree.heading('Estado', text='Estado')
        self.users_tree.heading('Fecha Inicio', text='Fecha Inicio')
        self.users_tree.heading('Fecha Fin', text='Fecha Fin')
        self.users_tree.heading('Observación', text='Observación')
        
        self.users_tree.column('ID', width=60)
        self.users_tree.column('General ID', width=100)
        self.users_tree.column('Estado', width=80)
        self.users_tree.column('Fecha Inicio', width=120)
        self.users_tree.column('Fecha Fin', width=120)
        self.users_tree.column('Observación', width=200)
        
        # Scrollbar para treeview
        scrollbar = ttk.Scrollbar(left_panel, orient='vertical', command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind selección
        self.users_tree.bind('<<TreeviewSelect>>', self.on_user_select)
        
        # Panel derecho: Acciones de usuario
        right_panel = ttk.LabelFrame(users_frame, text="  Acciones de Usuario  ", padding=10)
        right_panel.pack(side='right', fill='y', padx=(10, 0))
        right_panel.configure(width=300)
        
        # Info del usuario seleccionado
        self.user_info_label = ttk.Label(
            right_panel,
            text="👆 Seleccione un usuario para ver detalles\ny acciones disponibles",
            font=('Arial', 10),
            foreground='#7f8c8d',
            justify='center'
        )
        self.user_info_label.pack(pady=(0, 20))
        
        # Acciones
        actions_frame = ttk.LabelFrame(right_panel, text="  Acciones Disponibles  ", padding=10)
        actions_frame.pack(fill='x', pady=(0, 10))
        
        # Limpiar manualmente
        clean_btn = ttk.Button(
            actions_frame,
            text="🧹 Limpiar Chromium Manualmente",
            command=self.manual_clean_user,
            style='Action.TButton'
        )
        clean_btn.pack(fill='x', pady=5)
        
        # Ver detalles del usuario
        details_btn = ttk.Button(
            actions_frame,
            text="🔍 Ver Detalles Completos",
            command=self.view_user_details,
            style='Action.TButton'
        )
        details_btn.pack(fill='x', pady=5)
        
    def _create_exe_tab(self):
        """Crea la pestaña de generación de EXE"""
        exe_frame = ttk.Frame(self.notebook)
        self.notebook.add(exe_frame, text="📦 Generación de EXE")
        
        # Configuración de EXE
        config_frame = ttk.LabelFrame(exe_frame, text="  Configuración de EXE  ", padding=20)
        config_frame.pack(fill='x', padx=20, pady=20)
        
        # Usuario objetivo - con validación
        ttk.Label(config_frame, text="Usuario Objetivo (Practitioner ID):").grid(row=0, column=0, sticky='w', pady=5)
        user_frame = ttk.Frame(config_frame)
        user_frame.grid(row=0, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        self.exe_user_id = tk.StringVar(value="")  # Inicializar explícitamente
        self.user_id_entry = ttk.Entry(user_frame, textvariable=self.exe_user_id, width=15)
        self.user_id_entry.pack(side='left')
        
        # Debug: Verificar que el Entry esté funcionando
        print(f"DEBUG INIT: Entry creado con variable: {self.exe_user_id}")
        print(f"DEBUG INIT: Entry widget: {self.user_id_entry}")
        
        # SIN binding automático - solo validación manual
        validate_btn = ttk.Button(
            user_frame,
            text="🔍 Validar",
            command=lambda: self.manual_validate_user_id_fixed(),
            width=10
        )
        validate_btn.pack(side='left', padx=(5, 0))
        
        self.user_validation_label = ttk.Label(
            user_frame,
            text="",
            foreground='#7f8c8d',
            font=('Arial', 9)
        )
        self.user_validation_label.pack(side='left', padx=(10, 0))
        
        # Fecha de fin de convenio (automática desde BD)
        ttk.Label(config_frame, text="Fecha Fin de Convenio:").grid(row=1, column=0, sticky='w', pady=5)
        self.date_info_label = ttk.Label(
            config_frame,
            text="🔍 Seleccione un usuario para ver su fecha",
            font=('Arial', 9),
            foreground='#7f8c8d'
        )
        self.date_info_label.grid(row=1, column=1, pady=5, padx=(10, 0), sticky='w')
        
        # Modo de limpieza
        ttk.Label(config_frame, text="Modo de Limpieza:").grid(row=2, column=0, sticky='w', pady=5)
        self.clean_mode_var = tk.StringVar(value="profile")
        mode_combo = ttk.Combobox(
            config_frame,
            textvariable=self.clean_mode_var,
            values=['profile', 'files'],
            width=30,
            state='readonly'
        )
        mode_combo.grid(row=2, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        # Configurar grid
        config_frame.columnconfigure(1, weight=1)
        
        # Acciones de EXE
        actions_frame = ttk.LabelFrame(exe_frame, text="  Acciones  ", padding=20)
        actions_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        generate_exe_btn = ttk.Button(
            actions_frame,
            text="🚀 Generar EXE Personalizado",
            command=self.generate_custom_exe,
            style='Action.TButton'
        )
        generate_exe_btn.pack(side='left', padx=(0, 10))
        
        validate_config_btn = ttk.Button(
            actions_frame,
            text="🔍 Validar Configuración",
            command=self.validate_exe_config
        )
        validate_config_btn.pack(side='left', padx=(0, 10))
        
        clear_log_btn = ttk.Button(
            actions_frame,
            text="🧹 Limpiar Log",
            command=self.clear_exe_log
        )
        clear_log_btn.pack(side='left')
        
        # Log de generación
        log_frame = ttk.LabelFrame(exe_frame, text="  Log de Generación  ", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.exe_log = tk.Text(log_frame, height=10, font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.exe_log.yview)
        self.exe_log.configure(yscrollcommand=log_scrollbar.set)
        
        self.exe_log.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
    def _create_config_tab(self):
        """Crea la pestaña de configuración global"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuración")
        
        # Configuración global
        global_frame = ttk.LabelFrame(config_frame, text="  Configuración Global  ", padding=20)
        global_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(global_frame, text="Horario Global de Limpieza:").grid(row=0, column=0, sticky='w', pady=5)
        
        global_time_frame = ttk.Frame(global_frame)
        global_time_frame.grid(row=0, column=1, pady=5, padx=(10, 0), sticky='ew')
        
        self.global_hour_var = tk.StringVar(value="14")
        global_hour_spin = ttk.Spinbox(global_time_frame, from_=0, to=23, textvariable=self.global_hour_var, width=5)
        global_hour_spin.pack(side='left')
        
        ttk.Label(global_time_frame, text=":").pack(side='left', padx=5)
        
        self.global_minute_var = tk.StringVar(value="00")
        global_minute_spin = ttk.Spinbox(global_time_frame, from_=0, to=59, textvariable=self.global_minute_var, width=5)
        global_minute_spin.pack(side='left')
        
        update_global_btn = ttk.Button(
            global_frame,
            text="🔄 Actualizar Horario Global",
            command=self.update_global_schedule
        )
        update_global_btn.grid(row=1, column=0, columnspan=2, pady=20)
        
        global_frame.columnconfigure(1, weight=1)
        
    def _create_status_bar(self):
        """Crea la barra de estado"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="✅ Conectado - Listo para administrar")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=('Arial', 9),
            foreground='#27ae60'
        )
        status_label.pack(side='left')
        
        # Hora actual
        self.time_var = tk.StringVar()
        time_label = ttk.Label(
            status_frame,
            textvariable=self.time_var,
            font=('Arial', 9),
            foreground='#7f8c8d'
        )
        time_label.pack(side='right')
        
        self._update_time()
        
    def _update_time(self):
        """Actualiza la hora en la barra de estado"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(f"🕒 {current_time}")
        self.root.after(1000, self._update_time)
        
    def refresh_practitioners(self):
        """Actualiza la lista de usuarios"""
        try:
            self.status_var.set("🔄 Actualizando lista de usuarios...")
            
            # Obtener todos los usuarios
            practitioners = self.db_service.get_all_practitioners()
            self.practitioners_data = practitioners
            
            # Limpiar treeview
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Agregar usuarios al treeview
            max_id = self.max_seen_id
            for practitioner in practitioners:
                status_text = "✅ Activo" if practitioner.get('practitioner_status') == 'A' else "❌ Inactivo"
                
                # Formatear fechas si existen
                fecha_inicio = practitioner.get('practitioner_date_start', '')
                fecha_fin = practitioner.get('practitioner_date_end', '')
                if fecha_inicio:
                    fecha_inicio = str(fecha_inicio)
                if fecha_fin:
                    fecha_fin = str(fecha_fin)
                
                self.users_tree.insert('', 'end', values=(
                    practitioner.get('practitioner_id'),
                    practitioner.get('general_id', 'N/A'),
                    status_text,
                    fecha_inicio,
                    fecha_fin,
                    practitioner.get('practitioner_observation', 'Sin observaciones')[:50] + ('...' if len(str(practitioner.get('practitioner_observation', ''))) > 50 else '')
                ))
                try:
                    pid = int(practitioner.get('practitioner_id'))
                    if pid > max_id:
                        max_id = pid
                except Exception:
                    pass
            
            # YA NO necesitamos combo de usuarios - usamos entrada de texto con validación
            # El campo Practitioner ID es ahora un Entry, no un Combobox
            
            # Guardar marcadores de sincronización
            from datetime import datetime
            self.last_full_sync_ts = datetime.now()
            self.max_seen_id = max_id

            self.status_var.set(f"✅ {len(practitioners)} usuarios cargados")
            
        except Exception as e:
            self.status_var.set("❌ Error actualizando usuarios")
            messagebox.showerror("Error", f"No se pudo actualizar la lista de usuarios:\n{e}")

    def refresh_selected_practitioner(self):
        """Refresca únicamente la fila del usuario seleccionado"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showinfo("Información", "Seleccione un usuario en la tabla para actualizar solo esa fila.")
            return

        item_id = selection[0]
        values = self.users_tree.item(item_id, 'values')
        if not values:
            return

        try:
            pid = int(values[0])
        except Exception:
            pid = values[0]

        try:
            self.status_var.set(f"🔁 Actualizando usuario {pid}...")
            data = self.db_service.get_practitioner_by_id(pid)
            if not data:
                messagebox.showwarning("No encontrado", f"El usuario {pid} ya no existe en la BD")
                # Eliminar la fila si ya no existe
                self.users_tree.delete(item_id)
                self.status_var.set(f"⚠️ Usuario {pid} eliminado de la lista")
                return

            status_text = "✅ Activo" if data.get('practitioner_status') == 'A' else "❌ Inactivo"
            fecha_inicio = str(data.get('practitioner_date_start', '')) if data.get('practitioner_date_start') else ''
            fecha_fin = str(data.get('practitioner_date_end', '')) if data.get('practitioner_date_end') else ''
            observacion = data.get('practitioner_observation', 'Sin observaciones')
            if observacion is None:
                observacion = 'Sin observaciones'
            obs_short = str(observacion)[:50] + ('...' if len(str(observacion)) > 50 else '')

            # Actualizar los valores de la fila seleccionada
            self.users_tree.item(item_id, values=(
                data.get('practitioner_id'),
                data.get('general_id', 'N/A'),
                status_text,
                fecha_inicio,
                fecha_fin,
                obs_short
            ))

            # También sincronizar el cache en memoria
            updated = False
            for idx, p in enumerate(self.practitioners_data):
                try:
                    cached_id = int(p.get('practitioner_id'))
                except Exception:
                    cached_id = p.get('practitioner_id')
                if cached_id == pid:
                    self.practitioners_data[idx] = data
                    updated = True
                    break
            if not updated:
                self.practitioners_data.append(data)

            self.status_var.set(f"✅ Usuario {pid} actualizado")
        except Exception as e:
            self.status_var.set("❌ Error actualizando usuario")
            messagebox.showerror("Error", f"No se pudo actualizar el usuario {pid}:\n{e}")

    def incremental_refresh(self):
        """Realiza una actualización incremental: añade nuevos IDs y actualiza filas cambiadas.
        Requiere columna updated_at para detectar actualizaciones; si no existe, solo añade nuevos.
        """
        try:
            added = 0
            updated = 0

            # 1) Nuevos registros por ID mayor al visto
            try:
                new_rows = self.db_service.get_new_practitioners_since_id(self.max_seen_id)
            except Exception as e:
                new_rows = []
                print(f"DEBUG INCR: error nuevos: {e}")

            for data in new_rows:
                status_text = "✅ Activo" if data.get('practitioner_status') == 'A' else "❌ Inactivo"
                fecha_inicio = str(data.get('practitioner_date_start', '')) if data.get('practitioner_date_start') else ''
                fecha_fin = str(data.get('practitioner_date_end', '')) if data.get('practitioner_date_end') else ''
                observacion = data.get('practitioner_observation', 'Sin observaciones')
                if observacion is None:
                    observacion = 'Sin observaciones'
                obs_short = str(observacion)[:50] + ('...' if len(str(observacion)) > 50 else '')

                # Evitar insertar duplicado si ya existe en la tabla
                existing_item = None
                for itm in self.users_tree.get_children():
                    vals = self.users_tree.item(itm, 'values')
                    if vals and str(vals[0]) == str(data.get('practitioner_id')):
                        existing_item = itm
                        break
                if existing_item:
                    self.users_tree.item(existing_item, values=(
                        data.get('practitioner_id'),
                        data.get('general_id', 'N/A'),
                        status_text,
                        fecha_inicio,
                        fecha_fin,
                        obs_short
                    ))
                else:
                    self.users_tree.insert('', 'end', values=(
                        data.get('practitioner_id'),
                        data.get('general_id', 'N/A'),
                        status_text,
                        fecha_inicio,
                        fecha_fin,
                        obs_short
                    ))

                # Actualizar caches
                self.practitioners_data.append(data)
                try:
                    pid = int(data.get('practitioner_id'))
                    if pid > self.max_seen_id:
                        self.max_seen_id = pid
                except Exception:
                    pass
                added += 1

            # 2) Actualizaciones por updated_at si está disponible
            updated_rows = []
            if self.last_full_sync_ts:
                try:
                    updated_rows = self.db_service.get_updated_practitioners_since_ts(self.last_full_sync_ts) or []
                except Exception as e:
                    updated_rows = []
                    print(f"DEBUG INCR: error updated_at: {e}")

            # Mapear filas actuales por ID para actualizar la UI
            if updated_rows:
                # Construir índice de items: pid -> item_id
                id_to_item = {}
                for item in self.users_tree.get_children():
                    vals = self.users_tree.item(item, 'values')
                    if vals:
                        try:
                            pid = int(vals[0])
                        except Exception:
                            pid = vals[0]
                        id_to_item[pid] = item

                for data in updated_rows:
                    try:
                        pid = int(data.get('practitioner_id'))
                    except Exception:
                        pid = data.get('practitioner_id')
                    item_id = id_to_item.get(pid)
                    if not item_id:
                        continue  # si no está en la tabla (alta nueva), ya lo cubre el paso 1

                    status_text = "✅ Activo" if data.get('practitioner_status') == 'A' else "❌ Inactivo"
                    fecha_inicio = str(data.get('practitioner_date_start', '')) if data.get('practitioner_date_start') else ''
                    fecha_fin = str(data.get('practitioner_date_end', '')) if data.get('practitioner_date_end') else ''
                    observacion = data.get('practitioner_observation', 'Sin observaciones')
                    if observacion is None:
                        observacion = 'Sin observaciones'
                    obs_short = str(observacion)[:50] + ('...' if len(str(observacion)) > 50 else '')

                    self.users_tree.item(item_id, values=(
                        data.get('practitioner_id'),
                        data.get('general_id', 'N/A'),
                        status_text,
                        fecha_inicio,
                        fecha_fin,
                        obs_short
                    ))

                    # Sync cache
                    for idx, p in enumerate(self.practitioners_data):
                        try:
                            cached_id = int(p.get('practitioner_id'))
                        except Exception:
                            cached_id = p.get('practitioner_id')
                        if cached_id == pid:
                            self.practitioners_data[idx] = data
                            updated += 1
                            break

            # Actualizar marcador de sync
            from datetime import datetime
            self.last_full_sync_ts = datetime.now()

            self.status_var.set(f"⚡ Incremental: +{added} nuevos, {updated} actualizados")
        except Exception as e:
            self.status_var.set("❌ Error en actualización incremental")
            messagebox.showerror("Error", f"No se pudo completar la actualización incremental:\n{e}")

    def smart_refresh(self):
        """Refresca de forma inteligente: actualiza solo filas nuevas o modificadas, sin full reload.
        No requiere columnas adicionales en la BD.
        """
        try:
            self.status_var.set("🔄 Analizando cambios...")
            self.root.update_idletasks()

            # 1) Obtener firmas ligeras desde BD
            signatures = self.db_service.get_practitioner_signatures()

            # 2) Construir índices de UI y cache
            id_to_item = {}
            for item in self.users_tree.get_children():
                vals = self.users_tree.item(item, 'values')
                if vals:
                    try:
                        pid = int(vals[0])
                    except Exception:
                        pid = vals[0]
                    id_to_item[pid] = item

            cache_index = {}
            for p in self.practitioners_data:
                try:
                    pid = int(p.get('practitioner_id'))
                except Exception:
                    pid = p.get('practitioner_id')
                cache_index[pid] = p

            added = 0
            updated = 0

            # 3) Recorrer firmas para detectar altas/cambios
            for sig in signatures:
                try:
                    pid = int(sig.get('practitioner_id'))
                except Exception:
                    pid = sig.get('practitioner_id')

                item_id = id_to_item.get(pid)
                cached = cache_index.get(pid)

                # Calcular firma cache actual
                def to_signature(d):
                    if not d:
                        return None
                    return (
                        d.get('general_id'),
                        d.get('practitioner_status'),
                        str(d.get('practitioner_date_start')) if d.get('practitioner_date_start') else '',
                        str(d.get('practitioner_date_end')) if d.get('practitioner_date_end') else ''
                    )

                sig_new = to_signature(sig)
                sig_old = to_signature(cached)

                if item_id is None:
                    # Alta nueva: pedir fila completa y añadir
                    data = self.db_service.get_practitioner_by_id(pid)
                    if not data:
                        continue
                    status_text = "✅ Activo" if data.get('practitioner_status') == 'A' else "❌ Inactivo"
                    fecha_inicio = str(data.get('practitioner_date_start', '')) if data.get('practitioner_date_start') else ''
                    fecha_fin = str(data.get('practitioner_date_end', '')) if data.get('practitioner_date_end') else ''
                    observacion = data.get('practitioner_observation', 'Sin observaciones')
                    if observacion is None:
                        observacion = 'Sin observaciones'
                    obs_short = str(observacion)[:50] + ('...' if len(str(observacion)) > 50 else '')

                    # Evitar insertar duplicado si ya existe en la tabla
                    existing_item = None
                    for itm in self.users_tree.get_children():
                        vals = self.users_tree.item(itm, 'values')
                        if vals and str(vals[0]) == str(data.get('practitioner_id')):
                            existing_item = itm
                            break
                    if existing_item:
                        self.users_tree.item(existing_item, values=(
                            data.get('practitioner_id'),
                            data.get('general_id', 'N/A'),
                            status_text,
                            fecha_inicio,
                            fecha_fin,
                            obs_short
                        ))
                    else:
                        self.users_tree.insert('', 'end', values=(
                            data.get('practitioner_id'),
                            data.get('general_id', 'N/A'),
                            status_text,
                            fecha_inicio,
                            fecha_fin,
                            obs_short
                        ))
                    self.practitioners_data.append(data)
                    try:
                        pid_int = int(data.get('practitioner_id'))
                        if pid_int > self.max_seen_id:
                            self.max_seen_id = pid_int
                    except Exception:
                        pass
                    added += 1
                else:
                    # Existe en UI: si la firma cambió, refrescar esa fila
                    if sig_new != sig_old:
                        data = self.db_service.get_practitioner_by_id(pid)
                        if not data:
                            # Si ya no existe, eliminar fila
                            self.users_tree.delete(item_id)
                            continue
                        status_text = "✅ Activo" if data.get('practitioner_status') == 'A' else "❌ Inactivo"
                        fecha_inicio = str(data.get('practitioner_date_start', '')) if data.get('practitioner_date_start') else ''
                        fecha_fin = str(data.get('practitioner_date_end', '')) if data.get('practitioner_date_end') else ''
                        observacion = data.get('practitioner_observation', 'Sin observaciones')
                        if observacion is None:
                            observacion = 'Sin observaciones'
                        obs_short = str(observacion)[:50] + ('...' if len(str(observacion)) > 50 else '')

                        self.users_tree.item(item_id, values=(
                            data.get('practitioner_id'),
                            data.get('general_id', 'N/A'),
                            status_text,
                            fecha_inicio,
                            fecha_fin,
                            obs_short
                        ))
                        # Sync cache
                        cache_index[pid] = data
                        for idx, p in enumerate(self.practitioners_data):
                            try:
                                cached_id = int(p.get('practitioner_id'))
                            except Exception:
                                cached_id = p.get('practitioner_id')
                            if cached_id == pid:
                                self.practitioners_data[idx] = data
                                break
                        updated += 1

            # 4) Actualizar marcadores y estado
            from datetime import datetime
            self.last_full_sync_ts = datetime.now()
            self.status_var.set(f"✅ Actualización inteligente: +{added} nuevos, {updated} modificados")
        except Exception as e:
            self.status_var.set("❌ Error en actualización inteligente")
            messagebox.showerror("Error", f"No se pudo completar la actualización:\n{e}")
    
    def show_inactive_only(self):
        """Muestra solo usuarios inactivos"""
        try:
            inactive_users = self.db_service.get_inactive_practitioners()
            
            # Limpiar treeview
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Agregar solo usuarios inactivos
            for user in inactive_users:
                fecha_inicio = str(user.get('practitioner_date_start', ''))
                fecha_fin = str(user.get('practitioner_date_end', ''))
                
                self.users_tree.insert('', 'end', values=(
                    user.get('practitioner_id'),
                    user.get('general_id', 'N/A'),
                    "❌ Inactivo",
                    fecha_inicio,
                    fecha_fin,
                    user.get('practitioner_observation', 'Sin observaciones')[:50] + ('...' if len(str(user.get('practitioner_observation', ''))) > 50 else '')
                ))
            
            self.status_var.set(f"⚠️ Mostrando {len(inactive_users)} usuarios inactivos")
            self.showing_inactives = True
            self.toggle_inactive_btn.config(text="👁️ Mostrar Todo")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar usuarios inactivos:\n{e}")

    def toggle_inactives(self):
        """Alterna entre mostrar solo inactivos y mostrar todos desde cache."""
        if not self.showing_inactives:
            # Pasar a solo inactivos (consulta puntual)
            self.show_inactive_only()
        else:
            # Volver a mostrar todo desde cache (sin consultar toda la BD)
            try:
                # Limpiar treeview
                for item in self.users_tree.get_children():
                    self.users_tree.delete(item)

                # Repintar desde cache existente
                count = 0
                for practitioner in self.practitioners_data:
                    status_text = "✅ Activo" if practitioner.get('practitioner_status') == 'A' else "❌ Inactivo"
                    fecha_inicio = practitioner.get('practitioner_date_start', '')
                    fecha_fin = practitioner.get('practitioner_date_end', '')
                    if fecha_inicio:
                        fecha_inicio = str(fecha_inicio)
                    if fecha_fin:
                        fecha_fin = str(fecha_fin)

                    self.users_tree.insert('', 'end', values=(
                        practitioner.get('practitioner_id'),
                        practitioner.get('general_id', 'N/A'),
                        status_text,
                        fecha_inicio,
                        fecha_fin,
                        practitioner.get('practitioner_observation', 'Sin observaciones')[:50] + ('...' if len(str(practitioner.get('practitioner_observation', ''))) > 50 else '')
                    ))
                    count += 1

                self.status_var.set(f"✅ Mostrando todos ({count}) desde caché")
                self.showing_inactives = False
                self.toggle_inactive_btn.config(text="⚠️ Mostrar Inactivos")
            except Exception as e:
                self.status_var.set("❌ Error mostrando todos desde caché")
                messagebox.showerror("Error", f"No se pudo restaurar la vista completa:\n{e}")
    
    def on_user_select(self, event):
        """Maneja la selección de usuario"""
        selection = self.users_tree.selection()
        if selection:
            item = self.users_tree.item(selection[0])
            values = item['values']
            
            if values:
                user_id = values[0]
                general_id = values[1]
                user_status_text = values[2]
                fecha_inicio = values[3]
                fecha_fin = values[4]
                
                # Asegurar tipo consistente (int) para comparaciones posteriores
                try:
                    self.selected_practitioner = int(user_id)
                except Exception:
                    self.selected_practitioner = user_id
                
                # Mostrar información completa del usuario
                status_emoji = "✅" if "Activo" in user_status_text else "❌"
                self.user_info_label.config(
                    text=f"{status_emoji} Usuario ID: {user_id}\n"
                         f"🆔 General ID: {general_id}\n"
                         f"📅 Inicio: {fecha_inicio}\n"
                         f"⏰ Fin: {fecha_fin}\n"
                         f"📊 Estado: {user_status_text}"
                )
    
    def view_user_details(self):
        """Muestra detalles completos del usuario seleccionado"""
        if not self.selected_practitioner:
            messagebox.showwarning("Advertencia", "Seleccione un usuario primero")
            return
        
        try:
            # Buscar el usuario en la lista actual
            user_data = None
            for practitioner in self.practitioners_data:
                try:
                    pid = int(practitioner.get('practitioner_id'))
                except Exception:
                    pid = practitioner.get('practitioner_id')
                if pid == self.selected_practitioner:
                    user_data = practitioner
                    break
            
            if user_data:
                details = f"""
🆔 ID del Practicante: {user_data.get('practitioner_id')}
🆔 ID General: {user_data.get('general_id', 'N/A')}
📊 Estado: {'✅ Activo' if user_data.get('practitioner_status') == 'A' else '❌ Inactivo'}
📅 Fecha Inicio: {user_data.get('practitioner_date_start', 'N/A')}
⏰ Fecha Fin: {user_data.get('practitioner_date_end', 'N/A')}
🏢 Área ID: {user_data.get('area_id', 'N/A')}
🏬 División ID: {user_data.get('division_id', 'N/A')}
📝 Observaciones: {user_data.get('practitioner_observation', 'Sin observaciones')}
                """
                
                messagebox.showinfo("Detalles del Usuario", details.strip())
            else:
                messagebox.showerror("Error", "No se pudieron cargar los detalles del usuario")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo detalles:\n{e}")
    
    def manual_clean_user(self):
        """Ejecuta limpieza manual para el usuario"""
        if not self.selected_practitioner:
            messagebox.showwarning("Advertencia", "Seleccione un usuario primero")
            return
        
        result = messagebox.askyesno(
            "Confirmar Limpieza", 
            f"¿Está seguro de que desea ejecutar la limpieza manual para el usuario ID: {self.selected_practitioner}?\n\n"
            "Esta acción limpiará los datos de Chromium del usuario."
        )
        
        if result:
            # Aquí iría la lógica de limpieza manual
            messagebox.showinfo("Limpieza Iniciada", f"Limpieza manual iniciada para usuario {self.selected_practitioner}")
            self.status_var.set(f"🧹 Limpieza manual ejecutada para usuario {self.selected_practitioner}")
    
    def manual_validate_user_id(self):
        """Validación MANUAL del Usuario Objetivo con fecha automática de BD"""
        # Debug extra para verificar el problema
        raw_value = self.exe_user_id.get()
        
        # Método alternativo: leer directamente del widget
        try:
            widget_value = self.user_id_entry.get()
            print(f"DEBUG VALIDACION: Valor desde widget: '{widget_value}'")
        except:
            widget_value = ""
            print("DEBUG VALIDACION: No se pudo leer desde widget")
        
        user_id = raw_value.strip() if raw_value else ""
        
        print(f"DEBUG VALIDACION: Variable StringVar: '{raw_value}'")
        print(f"DEBUG VALIDACION: Variable stripped: '{user_id}'")
        print(f"DEBUG VALIDACION: Widget directo: '{widget_value}'")
        
        # Si StringVar falla, usar widget directo
        if not user_id and widget_value:
            user_id = widget_value.strip()
            print(f"DEBUG VALIDACION: Usando valor de widget: '{user_id}'")
        
        # Limpiar etiquetas
        self.user_validation_label.config(text="", foreground='#7f8c8d')
        self.date_info_label.config(text="", foreground='#7f8c8d')
        
        if not user_id:
            self.user_validation_label.config(text="❌ Ingrese un ID", foreground='#e74c3c')
            self.date_info_label.config(text="🔍 Seleccione un usuario para ver su fecha", foreground='#7f8c8d')
            return
        
        try:
            user_id_int = int(user_id)
            
            # Refrescar datos de BD siempre
            try:
                self.practitioners_data = self.db_service.get_all_practitioners()
                print(f"DEBUG VALIDACION: BD actualizada - {len(self.practitioners_data)} usuarios")
            except Exception as db_error:
                self.user_validation_label.config(text="❌ Error conectando BD", foreground='#e74c3c')
                self.date_info_label.config(text="❌ Error de conexión", foreground='#e74c3c')
                print(f"DEBUG VALIDACION: Error BD: {db_error}")
                return
            
            # Buscar usuario específico
            user_found = False
            user_data = None
            
            for practitioner in self.practitioners_data:
                if practitioner.get('practitioner_id') == user_id_int:
                    user_found = True
                    user_data = practitioner
                    break
            
            if user_found:
                # Usuario encontrado - mostrar status
                status_text = "✅ Activo" if user_data.get('practitioner_status') == 'A' else "❌ Inactivo"
                self.user_validation_label.config(
                    text=f"✅ Usuario encontrado ({status_text})",
                    foreground='#27ae60'
                )
                
                # Obtener y mostrar fecha de fin de convenio
                fecha_fin = user_data.get('practitioner_date_end')
                if fecha_fin:
                    self.date_info_label.config(
                        text=f"📅 Fecha fin convenio: {fecha_fin}",
                        foreground='#2980b9'
                    )
                    # Guardar la fecha para usar en la generación
                    self.selected_end_date = str(fecha_fin)
                    print(f"DEBUG VALIDACION: Fecha fin convenio: {fecha_fin}")
                else:
                    self.date_info_label.config(
                        text="⚠️ Sin fecha de fin de convenio en BD",
                        foreground='#f39c12'
                    )
                    self.selected_end_date = None
                
                print(f"DEBUG VALIDACION: Usuario {user_id_int} ENCONTRADO - Status: {user_data.get('practitioner_status')}")
                
            else:
                self.user_validation_label.config(
                    text="❌ Usuario no encontrado en BD",
                    foreground='#e74c3c'
                )
                self.date_info_label.config(
                    text="❌ Usuario no existe",
                    foreground='#e74c3c'
                )
                self.selected_end_date = None
                print(f"DEBUG VALIDACION: Usuario {user_id_int} NO encontrado")
                
        except ValueError:
            self.user_validation_label.config(
                text="❌ ID debe ser numérico",
                foreground='#e74c3c'
            )
            self.date_info_label.config(
                text="❌ ID inválido",
                foreground='#e74c3c'
            )
            self.selected_end_date = None
            print(f"DEBUG VALIDACION: '{user_id}' no es numérico")
        except Exception as e:
            self.user_validation_label.config(
                text=f"❌ Error: {str(e)[:30]}",
                foreground='#e74c3c'
            )
            self.date_info_label.config(text="❌ Error interno", foreground='#e74c3c')
            self.selected_end_date = None
            print(f"DEBUG VALIDACION: Error general: {e}")
    
    def manual_validate_user_id_fixed(self):
        """Función de validación SIMPLIFICADA para solucionar el problema del input vacío"""
        try:
            # Método 1: Intentar StringVar
            user_id_str = ""
            try:
                user_id_str = self.exe_user_id.get().strip()
                print(f"DEBUG FIXED: StringVar method: '{user_id_str}'")
            except Exception as e1:
                print(f"DEBUG FIXED: StringVar failed: {e1}")
            
            # Método 2: Intentar widget directo
            if not user_id_str:
                try:
                    user_id_str = self.user_id_entry.get().strip()
                    print(f"DEBUG FIXED: Widget method: '{user_id_str}'")
                except Exception as e2:
                    print(f"DEBUG FIXED: Widget failed: {e2}")
            
            # Método 3: Forzar refresh y reintentar
            if not user_id_str:
                try:
                    self.root.update()
                    user_id_str = self.exe_user_id.get().strip()
                    print(f"DEBUG FIXED: After update: '{user_id_str}'")
                except Exception as e3:
                    print(f"DEBUG FIXED: Update method failed: {e3}")
            
            print(f"DEBUG FIXED: Final value: '{user_id_str}'")
            
            # Limpiar estado anterior y labels
            self.validated_exe_user = None
            self.selected_end_date = None
            self.user_validation_label.config(text="", foreground='#7f8c8d')
            self.date_info_label.config(text="", foreground='#7f8c8d')
            
            if not user_id_str:
                self.user_validation_label.config(text="❌ No se pudo leer el ID", foreground='#e74c3c')
                print("DEBUG FIXED: No se pudo obtener valor del input")
                return
            
            # Continuar con validación normal
            try:
                user_id_int = int(user_id_str)
                print(f"DEBUG FIXED: Converted to int: {user_id_int}")
                
                # Refrescar BD
                try:
                    self.practitioners_data = self.db_service.get_all_practitioners()
                    print(f"DEBUG FIXED: BD updated - {len(self.practitioners_data)} users")
                except Exception as db_error:
                    self.user_validation_label.config(text="❌ Error BD", foreground='#e74c3c')
                    print(f"DEBUG FIXED: DB error: {db_error}")
                    return
                
                # Buscar usuario
                user_found = False
                user_data = None
                
                for practitioner in self.practitioners_data:
                    if practitioner.get('practitioner_id') == user_id_int:
                        user_found = True
                        user_data = practitioner
                        break
                
                if user_found:
                    status_text = "✅ Activo" if user_data.get('practitioner_status') == 'A' else "❌ Inactivo"
                    self.user_validation_label.config(
                        text=f"✅ Usuario encontrado ({status_text})",
                        foreground='#27ae60'
                    )
                    
                    # Obtener fecha fin convenio
                    fecha_fin = user_data.get('practitioner_date_end')
                    if fecha_fin:
                        self.date_info_label.config(
                            text=f"📅 Fecha fin convenio: {fecha_fin}",
                            foreground='#2980b9'
                        )
                        self.selected_end_date = str(fecha_fin)
                    else:
                        self.date_info_label.config(
                            text="⚠️ Sin fecha de fin convenio",
                            foreground='#f39c12'
                        )
                        self.selected_end_date = None
                    
                    # GUARDAR USUARIO VALIDADO para botón "Validar Configuración"
                    self.validated_exe_user = {
                        'id': user_id_int,
                        'data': user_data,
                        'id_string': user_id_str
                    }
                    
                    print(f"DEBUG FIXED: User {user_id_int} found - Status: {user_data.get('practitioner_status')}")
                else:
                    self.user_validation_label.config(
                        text="❌ Usuario no encontrado",
                        foreground='#e74c3c'
                    )
                    self.date_info_label.config(text="❌ Usuario no existe", foreground='#e74c3c')
                    self.selected_end_date = None
                    self.validated_exe_user = None  # Limpiar usuario validado
                    print(f"DEBUG FIXED: User {user_id_int} NOT found")
                    
            except ValueError:
                self.user_validation_label.config(text="❌ ID debe ser numérico", foreground='#e74c3c')
                print(f"DEBUG FIXED: '{user_id_str}' is not numeric")
            
        except Exception as e:
            self.user_validation_label.config(text="❌ Error interno", foreground='#e74c3c')
            print(f"DEBUG FIXED: General error: {e}")

    def validate_exe_config(self):
        """Valida la configuración completa antes de generar EXE"""
        mode = self.clean_mode_var.get()
        
        self.exe_log.insert(tk.END, f"🔍 Validando configuración para generación EXE...\n")
        
        # 1. VALIDAR USUARIO (usar estado de validación)
        if not self.validated_exe_user:
            self.exe_log.insert(tk.END, "❌ ERROR: Debe validar un Practitioner ID primero\n")
            self.exe_log.insert(tk.END, "💡 SOLUCIÓN: Use el botón '🔍 Validar' en el campo Usuario Objetivo\n")
            self.exe_log.see(tk.END)
            return False
        
        # Usuario ya validado previamente
        user_id_int = self.validated_exe_user['id']
        user_data = self.validated_exe_user['data']
        
        # Usuario válido
        status_text = "Activo" if user_data.get('practitioner_status') == 'A' else "Inactivo"
        self.exe_log.insert(tk.END, f"✅ Usuario {user_id_int} válido ({status_text})\n")
        
        print(f"DEBUG CONFIG: Using validated user {user_id_int}, mode='{mode}'")
        
        # 2. VALIDAR FECHA (automática desde BD)
        if not self.selected_end_date:
            self.exe_log.insert(tk.END, "❌ ERROR: Usuario sin fecha de fin de convenio\n")
            self.exe_log.insert(tk.END, "💡 SOLUCIÓN: Contacte administración para asignar fecha\n")
            self.exe_log.see(tk.END)
            return False
        
        try:
            from datetime import datetime
            # Convertir fecha de BD a objeto datetime
            if isinstance(self.selected_end_date, str):
                # Formato típico de BD: 'YYYY-MM-DD'
                agreement_date = datetime.strptime(self.selected_end_date, '%Y-%m-%d')
            else:
                # Ya es un objeto date
                agreement_date = datetime.combine(self.selected_end_date, datetime.min.time())
            
            today = datetime.now()
            
            if agreement_date.date() < today.date():
                days_past = (today.date() - agreement_date.date()).days
                self.exe_log.insert(tk.END, f"⚠️ ADVERTENCIA: Convenio expiró hace {days_past} días\n")
            elif agreement_date.date() == today.date():
                self.exe_log.insert(tk.END, "⚠️ ADVERTENCIA: El convenio expira HOY\n")
            else:
                days_diff = (agreement_date.date() - today.date()).days
                self.exe_log.insert(tk.END, f"✅ Fecha válida - Convenio expira en {days_diff} días\n")
                
        except Exception as e:
            self.exe_log.insert(tk.END, f"❌ ERROR: Formato de fecha inválido - {str(e)}\n")
            self.exe_log.see(tk.END)
            return False
        
        # 3. VALIDAR MODO
        if not mode:
            mode = "profile"  # Valor por defecto
        self.exe_log.insert(tk.END, f"✅ Modo de limpieza: {mode}\n")
        
        self.exe_log.insert(tk.END, "✅ Configuración completa y válida para generar EXE\n")
        self.exe_log.insert(tk.END, "─" * 50 + "\n")
        self.exe_log.see(tk.END)
        
        return True
    
    def clear_exe_log(self):
        """Limpia el log de generación de EXE"""
        from datetime import datetime
        self.exe_log.delete(1.0, tk.END)
        self.exe_log.insert(tk.END, "📝 Log de generación EXE - Limpiado\n")
        self.exe_log.insert(tk.END, f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.exe_log.insert(tk.END, "─" * 50 + "\n")
    
    def generate_custom_exe(self):
        """Genera EXE personalizado"""
        if not self.validate_exe_config():
            return
        
        # Obtener configuración desde usuario validado
        if not self.validated_exe_user:
            self.exe_log.insert(tk.END, "❌ ERROR: Usuario no validado correctamente\n")
            return
        
        user_id = self.validated_exe_user['id']  # Usar ID del usuario validado
        mode = self.clean_mode_var.get()
        
        # Usar fecha de fin de convenio de la BD
        agreement_date_str = self.selected_end_date if isinstance(self.selected_end_date, str) else str(self.selected_end_date)
        date_clean = agreement_date_str.replace('-', '')  # YYYYMMDD
        
        # Generar nombre de archivo
        exe_filename = f"browser_cleaner_user_{user_id}_{date_clean}.exe"
        
        self.exe_log.insert(tk.END, f"🔧 Iniciando generación de EXE...\n")
        self.exe_log.insert(tk.END, f"📄 Archivo: {exe_filename}\n")
        
        try:
            from datetime import datetime
            
            # Aquí agregaríamos el registro a la BD
            self.exe_log.insert(tk.END, f"📝 Registrando en BD: Usuario {user_id}, Fecha: {agreement_date_str}\n")
            
            # Crear el archivo de configuración personalizado
            config_data = {
                "practitioner_id": int(user_id),
                "agreement_end_date": agreement_date_str,
                "clean_mode": mode,
                "generated_at": datetime.now().isoformat(),
                "heartbeat_url": "https://your-heartbeat-server.com/api/status"
            }
            
            # ⚠️ SIMULACIÓN - En desarrollo
            self.exe_log.insert(tk.END, "⚠️ MODO SIMULACIÓN - PyInstaller pendiente de implementar\n")
            import time
            for i in range(5):
                self.exe_log.insert(tk.END, f"⚙️ [SIMULANDO] Compilando... {(i+1)*20}%\n")
                self.exe_log.see(tk.END)
                self.root.update()
                time.sleep(0.3)
            
            # Simular éxito con advertencia
            self.exe_log.insert(tk.END, "✅ [SIMULACIÓN] EXE configuración preparada!\n")
            self.exe_log.insert(tk.END, f"⚠️ NOTA: Archivo NO creado físicamente aún\n")
            self.exe_log.insert(tk.END, f"📋 Ubicación futura: ./output/{exe_filename}\n")
            self.exe_log.insert(tk.END, "📋 El EXE incluye:\n")
            self.exe_log.insert(tk.END, f"   - Configuración para usuario {user_id}\n")
            self.exe_log.insert(tk.END, f"   - Fecha límite de acuerdo: {agreement_date_str}\n")
            self.exe_log.insert(tk.END, f"   - Modo de limpieza: {mode}\n")
            self.exe_log.insert(tk.END, "   - Sistema de heartbeat integrado\n")
            self.exe_log.insert(tk.END, "   - Auto-detección de IP y nombre de equipo\n")
            self.exe_log.insert(tk.END, "=" * 50 + "\n")
            self.exe_log.see(tk.END)
            
            messagebox.showinfo("Configuración Lista", 
                                f"✅ Configuración EXE preparada exitosamente:\n{exe_filename}\n\n"
                                "⚠️ NOTA: Archivo físico aún no creado\n"
                                "PyInstaller será implementado próximamente")
            
        except Exception as e:
            self.exe_log.insert(tk.END, f"❌ ERROR al generar EXE: {str(e)}\n")
            self.exe_log.see(tk.END)
            messagebox.showerror("Error", f"Error al generar EXE: {str(e)}")
        
    def test_exe_config(self):
        """Prueba la configuración del EXE"""
        self.exe_log.insert(tk.END, f"🧪 Ejecutando prueba de configuración...\n")
        
        if self.validate_exe_config():
            user_id = self.exe_user_id.get().strip()
            year = self.year_var.get()
            month = self.month_var.get()
            day = self.day_var.get()
            mode = self.clean_mode_var.get()
            
            self.exe_log.insert(tk.END, f"✅ PRUEBA EXITOSA\n")
            self.exe_log.insert(tk.END, f"📋 Configuración validada:\n")
            self.exe_log.insert(tk.END, f"   - Usuario: {user_id}\n")
            self.exe_log.insert(tk.END, f"   - Fecha: {year}-{month:02d}-{day:02d}\n")
            self.exe_log.insert(tk.END, f"   - Modo: {mode}\n")
            self.exe_log.insert(tk.END, "🎯 Listo para generar EXE\n")
        else:
            self.exe_log.insert(tk.END, f"❌ PRUEBA FALLIDA - Revise la configuración\n")
        
        self.exe_log.insert(tk.END, "─" * 50 + "\n")
        self.exe_log.see(tk.END)
        self.exe_log.insert(tk.END, "─" * 30 + "\n")
        
        self.exe_log.see(tk.END)
    
    def update_global_schedule(self):
        """Actualiza el horario global"""
        hour = self.global_hour_var.get()
        minute = self.global_minute_var.get()
        
        result = messagebox.askyesno(
            "Confirmar Cambio",
            f"¿Actualizar el horario global a {hour}:{minute}?\n\n"
            "Esto afectará a todos los usuarios con configuración global."
        )
        
        if result:
            # Aquí iría la lógica de actualización global
            messagebox.showinfo("Actualizado", f"Horario global actualizado a {hour}:{minute}")
            self.status_var.set(f"⚙️ Horario global actualizado: {hour}:{minute}")
    
    def on_closing(self):
        """Maneja el cierre de la ventana"""
        result = messagebox.askyesno("Cerrar", "¿Desea cerrar el panel de administración?")
        if result:
            if self.db_service:
                self.db_service.close()
            self.root.quit()
    
    def run(self):
        """Ejecuta la ventana principal"""
        self.root.mainloop()

if __name__ == "__main__":
    # Test independiente (requiere db_service)
    print("Ventana principal requiere conexión a BD")
    print("Ejecute desde login_window.py")