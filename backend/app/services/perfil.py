from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Usuario
from app.schemas.usuario import PerfilIn
from app.services.auth import checar_data_nascimento


def atualizar_perfil(
    db: Session, usuario: Usuario, dados: PerfilIn, agora: datetime, hoje: date
) -> Usuario:
    enviados = dados.model_fields_set
    if not enviados:
        return usuario
    if "data_nascimento" in enviados:
        checar_data_nascimento(dados.data_nascimento, hoje)
    for campo in enviados:
        setattr(usuario, campo, getattr(dados, campo))
    usuario.atualizado_em = agora
    db.commit()
    return usuario
