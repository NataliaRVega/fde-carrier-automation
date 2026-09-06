class CarrierSalesError(Exception):
	"""Base exception for carrier sales domain errors."""

class InvalidStateTransitionError(CarrierSalesError):
	"""Raised when the workflow attempts an invalid state transition."""

class AuthorizationError(CarrierSalesError):
    """Raised when an operation is attempted without required authorization."""