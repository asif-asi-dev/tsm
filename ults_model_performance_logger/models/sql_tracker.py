import logging
import traceback
import threading
import time
from psycopg2 import errors
from odoo import models
from odoo.sql_db import Cursor

_logger = logging.getLogger(__name__)
_thread_local = threading.local()

_original_execute = Cursor.execute


def _get_txn_context():
    """Get or create transaction-local context"""
    if not hasattr(_thread_local, "txn_context"):
        _thread_local.txn_context = []
    return _thread_local.txn_context


def _record_stack(model_name, operation, vals=None):
    """Record the ORM stack when write/create called"""
    stack = ''.join(traceback.format_stack(limit=25))
    _get_txn_context().append({
        'time': time.strftime('%H:%M:%S'),
        'model': model_name,
        'operation': operation,
        'vals': list(vals.keys()) if vals else [],
        'stack': stack,
    })


# --- Patch BaseModel.write and create ---

_original_write = models.BaseModel.write
_original_create = models.BaseModel.create


def _tracked_write(self, vals):
    """Record ORM write() stack"""
    try:
        _record_stack(self._name, 'write', vals)
    except Exception:
        pass
    return _original_write(self, vals)


def _tracked_create(self, vals_list):
    """Record ORM create() stack"""
    try:
        sample_vals = vals_list[0] if vals_list else {}
        _record_stack(self._name, 'create', sample_vals)
    except Exception:
        pass
    return _original_create(self, vals_list)


models.BaseModel.write = _tracked_write
models.BaseModel.create = _tracked_create


# --- Patch Cursor.execute to link back to ORM stack on SerializationFailure ---

def _tracked_execute(self, query, params=None, log_exceptions=None):
    try:
        return _original_execute(self, query, params, log_exceptions)
    except Exception as e:
        if isinstance(e, errors.SerializationFailure):
            context = getattr(_thread_local, "txn_context", [])
            ctx_text = ""
            if context:
                ctx_text = "\n".join([
                    f"[{c['time']}] {c['operation'].upper()} on {c['model']} fields {c['vals']}\n{c['stack']}"
                    for c in context[-3:]  # last 3 ORM calls
                ])
            else:
                ctx_text = "(No ORM context captured — likely a background flush)"
            _logger.error(
                f"\n🚨 SERIALIZATION FAILURE DETECTED 🚨\n"
                f"Query: {query}\n"
                f"Params: {params}\n"
                f"DB: {self.dbname}\n"
                f"PID: {self.connection.get_backend_pid() if self.connection else 'N/A'}\n"
                f"---------------------- ORM CALL HISTORY ----------------------\n"
                f"{ctx_text}\n"
                f"---------------------------------------------------------------"
            )
        raise


Cursor.execute = _tracked_execute

_logger.warning("🔍 ORM-level Serialization Tracker Enabled")
