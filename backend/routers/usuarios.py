from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from deps import get_usuario_from_token
from models import Rota, Usuario, Viagem
from schemas import UsuarioOut, UsuarioUpdate
from security import hash_password
from validation import validar_senha

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_usuario_from_token)):
    return UsuarioOut.model_validate(user)


@router.put("/me", response_model=UsuarioOut)
def atualizar_me(
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_usuario_from_token),
):
    if (
        dados.email
        and dados.email != user.email
        and db.query(Usuario).filter(Usuario.email == dados.email).first()
    ):
        raise HTTPException(status_code=400, detail="E-mail já está em uso por outro usuário")

    if dados.nome is not None:
        user.nome = dados.nome
    if dados.email is not None:
        user.email = dados.email
    if dados.cnh is not None:
        user.cnh = dados.cnh
    if dados.senha is not None and dados.senha.strip():
        validar_senha(dados.senha)
        user.senha_hash = hash_password(dados.senha)

    db.add(user)
    db.commit()
    db.refresh(user)
    return UsuarioOut.model_validate(user)


@router.delete("/me", status_code=204)
def deletar_me(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_usuario_from_token),
):
    rotas = db.query(Rota).filter(Rota.motorista_id == user.id).all()
    for rota in rotas:
        db.query(Viagem).filter(Viagem.rota_id == rota.id).delete()
        db.delete(rota)

    db.query(Viagem).filter(Viagem.passageiro_id == user.id).delete()
    db.delete(user)
    db.commit()
