from datetime import date, datetime

from sqlalchemy import Date, cast, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.painel import ranking_formas, serie_mensal, ultimos_meses
from app.erros import ErroApi
from app.models import AcaoAdmin, Divida, Lancamento, Sessao, Usuario
from app.models.acao_admin import ACAO_DESATIVAR_CONTA, ACAO_REATIVAR_CONTA, ACAO_RESET_SENHA
from app.models.lancamento import STATUS_REALIZADO
from app.models.usuario import INDICE_ADMIN_UNICO, PAPEL_ADMIN, PAPEL_USUARIO
from app.schemas.admin import (
    ContasOut,
    DadosAdmin,
    FormaOut,
    LancamentosOut,
    MesOut,
    ResumoAdminOut,
    SituacaoConta,
)
from app.services.senha import gerar_senha_temporaria, hash_senha


def _erro_admin_existente() -> ErroApi:
    return ErroApi(409, "administrador_existente", "Já existe um administrador.")


def criar_administrador(db: Session, dados: DadosAdmin, agora: datetime) -> tuple[Usuario, str]:
    """Cria o único administrador, com senha temporária e troca obrigatória no 1º login."""
    if db.scalar(select(Usuario.id).where(Usuario.papel == PAPEL_ADMIN)) is not None:
        raise _erro_admin_existente()

    senha = gerar_senha_temporaria()
    admin = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(senha),
        telefone=dados.telefone,
        cargo=dados.cargo,
        papel=PAPEL_ADMIN,
        troca_senha_obrigatoria=True,
        criado_em=agora,
        atualizado_em=agora,
    )
    db.add(admin)
    try:
        db.flush()
    except IntegrityError as erro:
        db.rollback()
        # O índice único resolve dois comandos simultâneos.
        if INDICE_ADMIN_UNICO in str(erro.orig):
            raise _erro_admin_existente() from None
        raise ErroApi(409, "email_ja_cadastrado", "Este e-mail já está cadastrado.") from None
    db.commit()
    return admin, senha


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


MESES_NO_RESUMO = 12


def listar_usuarios(
    db: Session, busca: str | None, situacao: SituacaoConta | None = None
) -> list[Usuario]:
    consulta = select(Usuario).where(Usuario.papel == PAPEL_USUARIO)
    if situacao is not None:
        consulta = consulta.where(Usuario.ativo.is_(situacao == "ativos"))
    if busca and busca.strip():
        padrao = f"%{_escapar_like(busca.strip())}%"
        consulta = consulta.where(
            or_(
                Usuario.nome.ilike(padrao, escape="\\"),
                Usuario.email.ilike(padrao, escape="\\"),
            )
        )
    return list(db.scalars(consulta.order_by(Usuario.nome, Usuario.id)))


def _aplicar_senha_temporaria(db: Session, usuario: Usuario, agora: datetime) -> str:
    """Troca a senha por uma temporária, derruba as sessões e exige troca no próximo login."""
    senha = gerar_senha_temporaria()
    usuario.senha_hash = hash_senha(senha)
    usuario.troca_senha_obrigatoria = True
    usuario.atualizado_em = agora
    db.execute(delete(Sessao).where(Sessao.usuario_id == usuario.id))
    return senha


def _conta_alvo(db: Session, usuario_id: int) -> Usuario:
    """Conta de usuário comum; a do administrador não é alvo de ações."""
    usuario = db.scalar(
        select(Usuario).where(Usuario.id == usuario_id, Usuario.papel == PAPEL_USUARIO)
    )
    if usuario is None:
        raise ErroApi(404, "nao_encontrado", "Conta não encontrada.")
    return usuario


def _registrar(db: Session, admin: Usuario, acao: str, usuario: Usuario, agora: datetime) -> None:
    db.add(AcaoAdmin(admin_id=admin.id, acao=acao, usuario_alvo_id=usuario.id, ocorrida_em=agora))


def resetar_senha(db: Session, admin: Usuario, usuario_id: int, agora: datetime) -> str:
    """Gera senha temporária, derruba as sessões, exige troca e registra a ação."""
    usuario = _conta_alvo(db, usuario_id)
    senha = _aplicar_senha_temporaria(db, usuario, agora)
    _registrar(db, admin, ACAO_RESET_SENHA, usuario, agora)
    db.commit()
    return senha


def definir_ativo(
    db: Session, admin: Usuario, usuario_id: int, ativo: bool, agora: datetime
) -> Usuario:
    """Desativa (derrubando as sessões) ou reativa a conta; registra só quando muda."""
    usuario = _conta_alvo(db, usuario_id)
    if usuario.ativo != ativo:
        usuario.ativo = ativo
        usuario.atualizado_em = agora
        if not ativo:
            db.execute(delete(Sessao).where(Sessao.usuario_id == usuario.id))
        _registrar(
            db, admin, ACAO_REATIVAR_CONTA if ativo else ACAO_DESATIVAR_CONTA, usuario, agora
        )
        db.commit()
    return usuario


def obter_resumo(db: Session, hoje: date) -> ResumoAdminOut:
    """Contagens globais de uso. Nunca soma valores nem agrupa por usuário."""
    total, ativas = db.execute(
        select(func.count(), func.count().filter(Usuario.ativo)).where(
            Usuario.papel == PAPEL_USUARIO
        )
    ).one()

    lancamentos, realizados = db.execute(
        select(func.count(), func.count().filter(Lancamento.status == STATUS_REALIZADO))
    ).one()

    meses = ultimos_meses(hoje, MESES_NO_RESUMO)
    ultimo = meses[-1]
    fim = date(ultimo.year + ultimo.month // 12, ultimo.month % 12 + 1, 1)
    mes = cast(func.date_trunc("month", Lancamento.data), Date)
    linhas = db.execute(
        select(mes, Lancamento.tipo, func.count())
        .where(
            Lancamento.status == STATUS_REALIZADO,
            Lancamento.data >= meses[0],
            Lancamento.data < fim,
        )
        .group_by(mes, Lancamento.tipo)
    ).all()

    formas = db.execute(
        select(Divida.forma_pagamento, func.count()).group_by(Divida.forma_pagamento)
    ).all()

    return ResumoAdminOut(
        contas=ContasOut(total=total, ativas=ativas, desativadas=total - ativas),
        lancamentos=LancamentosOut(
            total=lancamentos, realizados=realizados, previstos=lancamentos - realizados
        ),
        por_mes=[
            MesOut(mes=m.strftime("%Y-%m"), entradas=entradas, saidas=saidas)
            for m, entradas, saidas in serie_mensal({(m, tipo): n for m, tipo, n in linhas}, meses)
        ],
        dividas_por_forma=[
            FormaOut(forma=forma, quantidade=n) for forma, n in ranking_formas(dict(formas))
        ],
    )


def resetar_senha_do_administrador(db: Session, agora: datetime) -> str:
    """Recupera o acesso do administrador pelo servidor (comando `resetar-senha-admin`).

    Não entra no registro de ações: é operação de quem opera o servidor, não do painel.
    """
    admin = db.scalar(select(Usuario).where(Usuario.papel == PAPEL_ADMIN))
    if admin is None:
        raise ErroApi(404, "nao_encontrado", "Nenhum administrador cadastrado.")

    senha = _aplicar_senha_temporaria(db, admin, agora)
    db.commit()
    return senha
