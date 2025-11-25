import threading
import time
import uuid

class BaseMonitor:
    def __init__(self):
        self.active_monitors = {}  # Stores the active run_id for each key
        self.threads = {}

    def start_monitoring(self, key, target_func, interval=5, *args, **kwargs):
        # Generate a unique ID for this run
        run_id = str(uuid.uuid4())
        self.active_monitors[key] = run_id
        
        def _loop(current_run_id):
            # Check if this thread is still the active one for this key
            while self.active_monitors.get(key) == current_run_id:
                try:
                    target_func(*args, **kwargs)
                    # Sleep in small chunks to allow faster stopping
                    for _ in range(int(interval * 10)):
                        if self.active_monitors.get(key) != current_run_id:
                            break
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Error in monitoring loop for {key}: {e}")
                    time.sleep(interval)

        th = threading.Thread(target=_loop, args=(run_id,), daemon=True)
        self.threads[key] = th
        th.start()
        return True

    def stop_monitoring(self, key):
        if key in self.active_monitors:
            self.active_monitors[key] = None  # This will stop the loop
        if key in self.threads:
            self.threads.pop(key, None)
        return True

    def is_monitoring(self, key):
        return self.active_monitors.get(key) is not None
