import unicodedata


def normalizar(texto: str | None) -> str:
    """Remove acentos e caixa — usado para busca insensível a acento/caixa.

    'Jaicós, PI' → 'jaicos, pi'. Permite que o usuário ache 'Jaicós'
    digitando 'jaicos'.
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.casefold().strip()
