import threading

class AsyncTreeviewUpdater:
    def __init__(self, root, treeview, status_var=None):
        self.root = root
        self.tree = treeview
        self.status_var = status_var

    def update_status_background(self, items_dict, check_connection_func, get_db_info_func, status_format_func=None):
        threading.Thread(
            target=self._process_updates,
            args=(items_dict, check_connection_func, get_db_info_func, status_format_func),
            daemon=True
        ).start()

    def _process_updates(self, items_dict, check_connection_func, get_db_info_func, status_format_func):
        total = 0
        connected = 0
        monitoring = 0
        
        for key, info in list(items_dict.items()):
            db_info = get_db_info_func(key)
            if not db_info:
                continue
                
            is_connected = check_connection_func(key, info)
            status_icon = "Activo" if is_connected else "Inactivo"
            
            self.root.after(0, lambda k=key, v=status_icon: self._update_item_status(k, v))
            
            total += 1
            if is_connected:
                connected += 1
            if info.get('monitoreando', False):
                monitoring += 1
        
        if self.status_var and status_format_func:
            status_text = status_format_func(total, connected, monitoring)
            self.root.after(0, lambda: self.status_var.set(status_text))

    def _update_item_status(self, key, value):
        try:
            if self.tree.exists(key):
                self.tree.set(key, column="Estado", value=value)
        except Exception:
            pass

