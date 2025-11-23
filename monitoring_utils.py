import threading
import time

class BaseMonitor:
    def __init__(self):
        self.active_monitors = {}
        self.threads = {}

    def start_monitoring(self, key, target_func, interval=5, *args, **kwargs):
        if key in self.active_monitors and self.active_monitors[key]:
            return False

        self.active_monitors[key] = True
        
        def _loop():
            while self.active_monitors.get(key, False):
                try:
                    target_func(*args, **kwargs)
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring loop for {key}: {e}")
                    time.sleep(interval)

        th = threading.Thread(target=_loop, daemon=True)
        self.threads[key] = th
        th.start()
        return True

    def stop_monitoring(self, key):
        if key in self.active_monitors:
            self.active_monitors[key] = False
        if key in self.threads:
            self.threads.pop(key, None)
        return True

    def is_monitoring(self, key):
        return self.active_monitors.get(key, False)
import threading
import time

class BaseMonitor:
    def __init__(self):
        self.active_monitors = {}
        self.threads = {}

    def start_monitoring(self, key, target_func, interval=5, *args, **kwargs):
        if key in self.active_monitors and self.active_monitors[key]:
            return False

        self.active_monitors[key] = True
        
        def _loop():
            while self.active_monitors.get(key, False):
                try:
                    target_func(*args, **kwargs)
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring loop for {key}: {e}")
                    time.sleep(interval)

        th = threading.Thread(target=_loop, daemon=True)
        self.threads[key] = th
        th.start()
        return True

    def stop_monitoring(self, key):
        if key in self.active_monitors:
            self.active_monitors[key] = False
        if key in self.threads:
            self.threads.pop(key, None)
        return True

    def is_monitoring(self, key):
        return self.active_monitors.get(key, False)
