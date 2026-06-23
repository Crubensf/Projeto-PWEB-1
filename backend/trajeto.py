"""Estimativa de duração de trajeto a partir das coordenadas.

Sem depender de serviço externo: usa distância de Haversine ajustada por um
fator de sinuosidade das estradas e uma velocidade média de van intermunicipal.
"""

import math

# Estradas reais são mais longas que a linha reta — fator típico ~1.3.
FATOR_RODOVIA = 1.3
# Velocidade média de van em rodovias do interior (com paradas): ~55 km/h.
VELOCIDADE_MEDIA_KMH = 55.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0  # raio da Terra em km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def duracao_estimada_min(
    origem_lat: float | None,
    origem_lng: float | None,
    destino_lat: float | None,
    destino_lng: float | None,
) -> int | None:
    """Minutos estimados de viagem; None se faltar alguma coordenada."""
    if None in (origem_lat, origem_lng, destino_lat, destino_lng):
        return None
    dist_km = haversine_km(origem_lat, origem_lng, destino_lat, destino_lng) * FATOR_RODOVIA
    minutos = dist_km / VELOCIDADE_MEDIA_KMH * 60
    return max(1, round(minutos))


def hora_mais_minutos(hora: str | None, minutos: int | None) -> str | None:
    """Soma minutos a um horário 'HH:MM'. Retorna 'HH:MM' (cap em 23:59)."""
    if not hora or minutos is None:
        return None
    try:
        h, m = map(int, hora.split(":"))
    except (ValueError, AttributeError):
        return None
    total = h * 60 + m + minutos
    total = min(total, 23 * 60 + 59)
    return f"{total // 60:02d}:{total % 60:02d}"
