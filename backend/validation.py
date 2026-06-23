from fastapi import HTTPException

from config import settings

PERFIS_VALIDOS = ("estudante", "motorista")


def validar_senha(senha: str) -> None:
    if not senha or len(senha) < settings.min_senha:
        raise HTTPException(
            status_code=400,
            detail=f"A senha deve ter no mínimo {settings.min_senha} caracteres.",
        )
    if not any(c.isalpha() for c in senha):
        raise HTTPException(
            status_code=400,
            detail="A senha deve conter pelo menos uma letra.",
        )
    if not any(c.isdigit() for c in senha):
        raise HTTPException(
            status_code=400,
            detail="A senha deve conter pelo menos um dígito.",
        )


def validar_perfil(perfil: str) -> None:
    if perfil not in PERFIS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Perfil inválido. Use um de: {', '.join(PERFIS_VALIDOS)}.",
        )


def validar_cnh(cnh: str | None) -> None:
    if not cnh or not cnh.isdigit() or len(cnh) != 11:
        raise HTTPException(
            status_code=400,
            detail="CNH deve ter exatamente 11 dígitos numéricos.",
        )
