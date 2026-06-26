"""Compatibility wrapper for Panasonic EMS2 API exceptions."""

from ..api.errors import (
    Ems2BaseException,
    Ems2ExceedRateLimit,
    Ems2Expectation,
    Ems2InvalidRefreshToken,
    Ems2LoginFailed,
    Ems2TokenExpired,
    Ems2TokenNotFound,
    Ems2TooManyRequest,
)

__all__ = [
    "Ems2BaseException",
    "Ems2TokenNotFound",
    "Ems2TokenExpired",
    "Ems2InvalidRefreshToken",
    "Ems2TooManyRequest",
    "Ems2LoginFailed",
    "Ems2Expectation",
    "Ems2ExceedRateLimit",
]
