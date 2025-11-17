"""
Odoo Field & Function Performance Profiler
Tracks execution time for computed fields, onchanges, and methods

Installation:
1. Add to your custom module: models/field_profiler.py
2. Import in __init__.py: from . import field_profiler
3. Restart Odoo
"""

import time
import logging
import functools
from odoo import models, api, fields as odoo_fields
import inspect
import traceback

_logger = logging.getLogger(__name__)

# ============================================================
# Configuration
# ============================================================
SLOW_THRESHOLD = 0.1          # Log operations > 100ms
TRACK_COMPUTED_FIELDS = True  # Track @api.depends fields
TRACK_ONCHANGE = True         # Track @api.onchange methods
TRACK_CONSTRAINTS = True      # Track @api.constrains
TRACK_REGULAR_METHODS = False # Track all methods (very verbose!)

# Models to track (empty = track all)
TRACKED_MODELS = [
    'purchase.order',
    'purchase.order.line',
    'sale.order.line',
    'stock.move',
    'stock.picking',
    'product.product',
    'res.users',
]

# Fields to specifically track (if you know suspects)
TRACKED_FIELDS = [
    # 'purchase.order.amount_total',
    # 'stock.move.state',
    # Add specific fields here
]

# ============================================================
# Field Computation Tracker
# ============================================================
_original_compute_field_value = models.BaseModel._compute_field_value

def _tracked_compute_field_value(self, field):
    """Track computed field execution time and log the caller location"""
    start = time.time()
    result = _original_compute_field_value(self, field)
    duration = time.time() - start

    if duration > SLOW_THRESHOLD:

        # Identify where the compute was triggered
        stack = traceback.format_stack()
        # or if you prefer showing FIRST caller outside compute methods:
        caller = next(
            (f for f in stack if "/addons/" in f and "_compute_" not in f),
            stack[-1]
        )

        compute_method = (
            field.compute if isinstance(field.compute, str) else field.compute.__name__
        )

        _logger.warning(
            "\n============ 🔥 SLOW COMPUTE DETECTED ============\n"
            f"Model: {self._name}\n"
            f"Field: {field.name}\n"
            f"Method: {compute_method}\n"
            f"Duration: {duration:.4f}s\n"
            f"Record IDs: {self.ids[:10]}\n"
            f"----------------------------------------------\n"
            f"Triggered from:\n{caller}"
            "=================================================\n"
        )

    return result

models.BaseModel._compute_field_value = _tracked_compute_field_value



# ============================================================
# Decorator Wrapper for @api.depends, @api.onchange, @api.constrains
# ============================================================
def create_tracking_wrapper(original_decorator, decorator_name, check_enabled):
    """Create a wrapper for Odoo decorators that tracks execution time"""

    def wrapper(*depends_args, **depends_kwargs):
        # Call original decorator
        original_wrapped = original_decorator(*depends_args, **depends_kwargs)

        # If it returns a decorator function, wrap that
        if callable(original_wrapped):
            def method_wrapper(func):
                # First apply the original decorator
                decorated_func = original_wrapped(func)

                # Then wrap with timing
                @functools.wraps(func)
                def timed_execution(self, *args, **kwargs):
                    # Check if tracking is enabled
                    if not check_enabled():
                        return decorated_func(self, *args, **kwargs)

                    # Check if model should be tracked
                    if TRACKED_MODELS and hasattr(self, '_name') and self._name not in TRACKED_MODELS:
                        return decorated_func(self, *args, **kwargs)

                    start = time.time()
                    result = decorated_func(self, *args, **kwargs)
                    duration = time.time() - start

                    if duration > SLOW_THRESHOLD:
                        model_name = self._name if hasattr(self, '_name') else 'Unknown'
                        _logger.warning(
                            f"🐌 SLOW {decorator_name.upper()}: {model_name}.{func.__name__}\n"
                            f"   Duration: {duration:.4f}s\n"
                            f"   Records: {len(self) if hasattr(self, '__len__') else 1}\n"
                            f"   Decorator args: {depends_args}"
                        )

                    return result

                return timed_execution

            return method_wrapper

        # If it's already a function (shouldn't happen but be safe)
        return original_wrapped

    return wrapper


# Apply decorator tracking
if TRACK_COMPUTED_FIELDS:
    _original_depends = api.depends
    api.depends = create_tracking_wrapper(_original_depends, 'depends', lambda: TRACK_COMPUTED_FIELDS)

if TRACK_ONCHANGE:
    _original_onchange = api.onchange
    api.onchange = create_tracking_wrapper(_original_onchange, 'onchange', lambda: TRACK_ONCHANGE)

if TRACK_CONSTRAINTS:
    _original_constrains = api.constrains
    api.constrains = create_tracking_wrapper(_original_constrains, 'constrains', lambda: TRACK_CONSTRAINTS)


# ============================================================
# Track write() to see which field updates are slow
# ============================================================
_original_write = models.BaseModel.write

def _tracked_write_with_fields(self, vals):
    """Track write operations and identify slow field updates"""
    if not vals or (TRACKED_MODELS and self._name not in TRACKED_MODELS):
        return _original_write(self, vals)

    start = time.time()

    # Write the values
    result = _original_write(self, vals)
    total_duration = time.time() - start

    if total_duration > SLOW_THRESHOLD:
        _logger.warning(
            f"🐌 SLOW WRITE: {self._name}\n"
            f"   Total Duration: {total_duration:.4f}s\n"
            f"   Records: {len(self)} (IDs: {self.ids[:10]})\n"
            f"   Fields Updated: {list(vals.keys())}\n"
            f"   Values: {str(vals)[:200]}"
        )

        # Try to identify which field caused the slowness
        # by checking related computed fields
        field_obj = self._fields
        computed_deps = []
        for field_name in vals.keys():
            if field_name in field_obj:
                field = field_obj[field_name]
                # Check if this field triggers computations
                if hasattr(field, 'related_field'):
                    computed_deps.append(f"{field_name} (related)")

        if computed_deps:
            _logger.info(f"   Triggered computed fields: {computed_deps}")

    return result

models.BaseModel.write = _tracked_write_with_fields


# ============================================================
# Track create() to see which field defaults are slow
# ============================================================
_original_create = models.BaseModel.create

@api.model_create_multi
def _tracked_create_with_fields(self, vals_list):
    """Track create operations and identify slow field defaults"""
    if not vals_list or (TRACKED_MODELS and self._name not in TRACKED_MODELS):
        return _original_create(self, vals_list)

    start = time.time()
    result = _original_create(self, vals_list)
    duration = time.time() - start

    if duration > SLOW_THRESHOLD:
        first_vals = vals_list[0] if vals_list else {}
        _logger.warning(
            f"🐌 SLOW CREATE: {self._name}\n"
            f"   Duration: {duration:.4f}s\n"
            f"   Record Count: {len(result) if hasattr(result, '__len__') else 1}\n"
            f"   Fields: {list(first_vals.keys())}\n"
            f"   Sample Values: {str(first_vals)[:200]}"
        )

    return result

models.BaseModel.create = _tracked_create_with_fields


# ============================================================
# Startup Message
# ============================================================
_logger.warning(
    f"🔍 Field & Function Profiler Enabled\n"
    f"   Threshold: {SLOW_THRESHOLD}s\n"
    f"   Computed Fields: {TRACK_COMPUTED_FIELDS}\n"
    f"   Onchange: {TRACK_ONCHANGE}\n"
    f"   Constraints: {TRACK_CONSTRAINTS}\n"
    f"   Regular Methods: {TRACK_REGULAR_METHODS}\n"
    f"   Tracked Models: {TRACKED_MODELS if TRACKED_MODELS else 'ALL'}"
)


# ============================================================
# Helper: Manual function profiling decorator
# ============================================================
def profile_function(func):
    """
    Decorator to manually profile any function

    Usage:
        from .field_profiler import profile_function

        @profile_function
        def my_slow_function(self):
            # your code
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.time()
        result = func(self, *args, **kwargs)
        duration = time.time() - start

        if duration > SLOW_THRESHOLD:
            model_name = self._name if hasattr(self, '_name') else 'Unknown'
            _logger.warning(
                f"🐌 PROFILED FUNCTION: {model_name}.{func.__name__}\n"
                f"   Duration: {duration:.4f}s"
            )

        return result

    return wrapper
