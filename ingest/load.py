"""Validation shared by the production snapshot loader."""
from decimal import Decimal, InvalidOperation
import json


class LoadError(ValueError):
    """Credential-free validation diagnostic; never includes raw source values."""


def token_rate(pricing, field):
    """Negative routing/unknown rates are not credits or usable token prices."""
    if pricing is None or pricing.get(field) is None:
        return None
    value = pricing[field]
    if not isinstance(value, str):
        raise LoadError('Token rates must be exact decimal strings')
    try:
        rate = Decimal(value)
    except InvalidOperation:
        raise LoadError('Invalid decimal token rate') from None
    if not rate.is_finite():
        raise LoadError('Non-finite token rate')
    if rate < 0:
        return None
    # PostgreSQL numeric: 131072 integer digits, 16383 fractional digits.
    # Inspect the exact tuple, not normalize()/quantize() (context rounding),
    # float conversion, or fixed-point formatting of enormous exponents.
    exponent = int(rate.as_tuple().exponent)
    if (exponent < -16383 or (rate and rate.adjusted() >= 131072)
            or (not rate and exponent > (2**31 - 1) // 2)):
        # Even zero's scientific exponent must fit PostgreSQL's text parser.
        raise LoadError('Token rate exceeds PostgreSQL numeric range')
    return rate


def _validate_json_strings(value):
    """Reject text PostgreSQL cannot store, without changing source content."""
    if isinstance(value, str):
        if '\x00' in value or any('\ud800' <= char <= '\udfff' for char in value):
            raise LoadError('JSON text contains NUL or invalid Unicode')
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_json_strings(key)
            _validate_json_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_json_strings(item)


def validate_metadata(row):
    """Reject wrong shapes; absent optional metadata remains SQL NULL."""
    try:
        json.dumps(row, allow_nan=False)
    except (TypeError, ValueError):
        raise LoadError('Invalid or non-finite raw JSON metadata') from None
    _validate_json_strings(row)
    for field in ('pricing', 'architecture', 'top_provider'):
        if row.get(field) is not None and not isinstance(row[field], dict):
            raise LoadError('Invalid metadata object')
    for obj, field, maximum in [
        (row, 'context_length', 9223372036854775807),
        (row, 'max_completion_tokens', 9223372036854775807),
        (row.get('top_provider') or {}, 'max_completion_tokens', 9223372036854775807),
        (row, 'created', 253402300799),
    ]:
        value = obj.get(field)
        if value is not None and (type(value) is not int or not 0 <= value <= maximum):
            raise LoadError('Invalid integer metadata range or type')
    for obj, field in [(row, 'supported_parameters'),
                       (row.get('architecture') or {}, 'input_modalities'),
                       (row.get('architecture') or {}, 'output_modalities')]:
        value = obj.get(field)
        if value is not None and (not isinstance(value, list) or any(not isinstance(x, str) for x in value)):
            raise LoadError('Metadata arrays must contain text values')
    slug = row.get('canonical_slug')
    if slug is not None and (not isinstance(slug, str) or not slug or any(c.isspace() for c in slug)):
        raise LoadError('Invalid canonical identifier; values are never repaired')
    if row.get('name') is not None and not isinstance(row['name'], str):
        raise LoadError('Metadata label must be text')
    token_rate(row.get('pricing'), 'prompt')
    token_rate(row.get('pricing'), 'completion')
