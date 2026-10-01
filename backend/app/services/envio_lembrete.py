"""Resumo diário dos lembretes por push. Roda por comando agendado, nunca numa requisição.

O transporte é injetado (`Enviador`) para o teste não depender de rede. Nada aqui registra
endpoint, chaves, valores ou textos: o relatório só tem contagens.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Protocol

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.lembrete import contar, situacao, texto_resumo
from app.models import EnvioLembrete, InscricaoPush, Usuario
from app.models.usuario import PAPEL_USUARIO
from app.services.lembrete import (
    livres_pendentes,
    origem_do_lancamento,
    pendencias_de_lancamento,
)

URL_LEMBRETES = "/lembretes"

ResultadoEnvio = Literal["ok", "expirado", "falha"]


class Enviador(Protocol):
    def enviar(self, inscricao: InscricaoPush, payload: dict[str, Any]) -> ResultadoEnvio:
        """`expirado`: o serviço de push recusou o aparelho de vez (404/410)."""
        ...


@dataclass
class Relatorio:
    usuarios: int = 0
    enviados: int = 0
    sem_pendencias: int = 0
    ja_enviados: int = 0
    removidos: int = 0
    falhas: int = 0


def _payload(db: Session, usuario_id: int, hoje: date) -> dict[str, Any] | None:
    itens = []
    for lancamento in pendencias_de_lancamento(db, usuario_id, hoje):
        sit = situacao(lancamento.data, hoje)
        if sit is not None:
            itens.append((origem_do_lancamento(lancamento), sit))
    for livre in livres_pendentes(db, usuario_id, hoje):
        sit = situacao(livre.data, hoje)
        if sit is not None:
            itens.append(("livre", sit))
    mensagem = texto_resumo(contar(itens), hoje)
    if mensagem is None:
        return None
    return {"titulo": mensagem.titulo, "corpo": mensagem.corpo, "url": URL_LEMBRETES}


def _reservar_dia(db: Session, usuario_id: int, hoje: date) -> bool:
    """Marca o dia antes de enviar; duas execuções simultâneas não enviam duas vezes."""
    reservado = db.scalar(
        insert(EnvioLembrete)
        .values(usuario_id=usuario_id, dia=hoje)
        .on_conflict_do_nothing()
        .returning(EnvioLembrete.usuario_id)
    )
    db.commit()
    return reservado is not None


def _ja_enviado(db: Session, usuario_id: int, hoje: date) -> bool:
    return db.get(EnvioLembrete, (usuario_id, hoje)) is not None


def enviar_lembretes_do_dia(db: Session, hoje: date, enviador: Enviador) -> Relatorio:
    """Um resumo por dia a cada usuário ativo com aparelho e algo atrasado ou a vencer."""
    relatorio = Relatorio()
    usuarios = db.scalars(
        select(Usuario.id)
        .where(
            Usuario.ativo.is_(True),
            Usuario.papel == PAPEL_USUARIO,
            select(InscricaoPush.id).where(InscricaoPush.usuario_id == Usuario.id).exists(),
        )
        .order_by(Usuario.id)
    ).all()

    for usuario_id in usuarios:
        relatorio.usuarios += 1
        if _ja_enviado(db, usuario_id, hoje):
            relatorio.ja_enviados += 1
            continue
        payload = _payload(db, usuario_id, hoje)
        if payload is None:
            relatorio.sem_pendencias += 1
            continue
        if not _reservar_dia(db, usuario_id, hoje):
            relatorio.ja_enviados += 1
            continue

        recebeu = False
        inscricoes = db.scalars(
            select(InscricaoPush)
            .where(InscricaoPush.usuario_id == usuario_id)
            .order_by(InscricaoPush.id)
        ).all()
        for inscricao in inscricoes:
            resultado = enviador.enviar(inscricao, payload)
            if resultado == "ok":
                recebeu = True
            elif resultado == "expirado":
                db.delete(inscricao)
                relatorio.removidos += 1

        if recebeu:
            relatorio.enviados += 1
        else:
            # Nenhum aparelho recebeu: libera o dia para a próxima execução tentar de novo.
            db.execute(
                delete(EnvioLembrete).where(
                    EnvioLembrete.usuario_id == usuario_id, EnvioLembrete.dia == hoje
                )
            )
            relatorio.falhas += 1
        db.commit()

    return relatorio
