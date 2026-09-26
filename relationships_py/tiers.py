from decimal import Decimal, InvalidOperation

APPROVED = {'approved_manual', 'approved_rule'}

def exclusion_reasons(amount, config):
    """Expose every material reason; a grey line never asserts a small deal."""
    reasons = []
    if amount.get('verification') not in APPROVED: reasons.append('unverified')
    if not amount.get('currency'): reasons.append('currency_unknown')
    elif amount['currency'] not in config: reasons.append('currency_unsupported')
    if amount.get('qualifier') not in ('exact', 'approximately'): reasons.append('bounded_or_unspecified')
    if amount.get('contingent') is True: reasons.append('conditional')
    elif amount.get('contingent') is not False: reasons.append('contingency_unknown')
    if amount.get('value_semantics') not in ('original_total', 'revised_total'): reasons.append('not_total')
    if amount.get('amount_kind') not in ('contract_value', 'committed_total', 'purchase_price', 'investment_amount'): reasons.append('unsupported_kind')
    try:
        n = Decimal(amount.get('value'))
        if not n.is_finite() or n < 0: reasons.append('value_unknown')
    except (InvalidOperation, TypeError, ValueError):
        if not any(amount.get(k) is not None for k in ('min_value', 'max_value')): reasons.append('value_unknown')
    return reasons

def tier(amount, config):
    """No FX, option summing, annualisation, or promotion of unknown values."""
    if exclusion_reasons(amount, config) or amount.get('value') is None:
        return None
    n = Decimal(amount['value'])
    rules = config[amount['currency']]
    index = max(i for i, bound in enumerate(rules['minimums']) if n >= Decimal(bound))
    return {'level': index + 1, 'color': rules['colors'][index], 'currency': amount['currency'], 'amount_id': amount['amount_id']}

def rating(amounts, config, disclosure='not_stated_in_source'):
    if not amounts:
        return {'tier': None, 'tier_reasons': [disclosure or 'ambiguous']}
    reasons = ['multiple_amounts'] if len(amounts) > 1 else []
    for amount in amounts:
        reasons.extend(exclusion_reasons(amount, config))
    return {'tier': tier(amounts[0], config) if len(amounts) == 1 else None,
            'tier_reasons': list(dict.fromkeys(reasons))}
