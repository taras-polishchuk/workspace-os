"""R7 drift-policy integration for the validator package.

The implementation remains owned by :mod:`workspace_os.policy`; this module is
only the stable validator namespace requested by R13.
"""
from workspace_os.policy import compute_drift_id, drift_categories, load_policy

__all__ = ["compute_drift_id", "drift_categories", "load_policy"]
