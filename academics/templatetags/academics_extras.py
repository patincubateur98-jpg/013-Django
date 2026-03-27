from django import template

register = template.Library()


@register.filter
def code_cours(value):
    code_brut = (str(value or '')).strip()
    if not code_brut:
        return '-'

    if code_brut.upper().startswith('PCNC'):
        chiffres = ''.join(ch for ch in code_brut if ch.isdigit())
        if len(chiffres) >= 3:
            return chiffres[-3:]
        parts = code_brut.split()
        if len(parts) > 1:
            return parts[-1]

    return code_brut
