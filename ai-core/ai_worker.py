import threading
from typing import Callable, Dict, Any

class AIWorker(threading.Thread):
    def __init__(
        self,
        service: Any,
        mode: str,
        payload: Dict[str, Any],
        callback: Callable[[str], None],
        error_callback: Callable[[str], None]
    ):
        super().__init__(daemon=True)
        self.service = service
        self.mode = mode
        self.payload = payload
        self.callback = callback
        self.error_callback = error_callback

    def run(self):
        try:
            result = ""
            if self.mode == "chat":
                msg = self.payload.get("message", "")
                result = self.service.chat(msg)
            elif self.mode == "agent":
                msg = self.payload.get("message", "")
                result = self.service.run_agent(msg)
            elif self.mode == "summarize":
                patient_id = self.payload.get("patient_id")
                result = self.service.summarize_patient_record(patient_id)
            elif self.mode == "diagnose":
                chief_complaint = self.payload.get("chief_complaint", "")
                patient_context = self.payload.get("patient_context", {})
                result = self.service.suggest_diagnoses(chief_complaint, patient_context)
            else:
                raise ValueError(f"Mode inconnu: {self.mode}")
            
            # Appelé via callback (qui fera widget.after pour être thread-safe avec Tkinter)
            self.callback(result)
        except Exception as e:
            self.error_callback(str(e))
