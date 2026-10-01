import math
from datetime import date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.login import calcular_bloqueio
from app.domain.usuario import MAX_EMAIL, validar_data_nascimento
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Sessao, TentativaLogin, Usuario
from app.models.usuario import PAPEL_ADMIN, PAPEL_USUARIO
from app.schemas.usuario import CadastroIn
from app.services.categoria import criar_categorias_iniciais
from app.services.senha import HASH_FICTICIO, hash_senha, precisa_rehash, verificar_senha
from app.services.sessao import criar_sessao, encerrar_outras_sessoes, encerrar_sessao

RETENCAO_FALHAS = timedelta(hours=24)


def checar_conta_editavel(usuario: Usuario) -> None:
    """Nome, e-mail e senha do administrador vêm do .env, que sempre vence."""
    if usuario.papel == PAPEL_ADMIN:
        raise ErroApi(
            403,
            "conta_gerenciada_no_servidor",
            "Os dados do administrador são definidos na configuração do servidor (.env).",
        )


def checar_data_nascimento(data: date | None, hoje: date) -> None:
    if data is None:
        return
    try:
        validar_data_nascimento(data, hoje)
    except ValueError as erro:
        raise ErroApi(
            422, "validacao", MENSAGEM_VALIDACAO, campos={"data_nascimento": str(erro)}
        ) from None


def cadastrar(db: Session, dados: CadastroIn, agora: datetime, hoje: date) -> tuple[Usuario, str]:
    """Cria a conta, as categorias iniciais e a sessão, numa transação."""
    checar_data_nascimento(dados.data_nascimento, hoje)
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        telefone=dados.telefone,
        cargo=dados.cargo,
        data_nascimento=dados.data_nascimento,
        papel=PAPEL_USUARIO,
        tipo_renda=dados.tipo_renda,
        criado_em=agora,
        atualizado_em=agora,
    )
    db.add(usuario)
    try:
        db.flush()
    except IntegrityError:
        # A restrição UNIQUE do e-mail resolve também cadastros simultâneos.
        db.rollback()
        raise ErroApi(409, "email_ja_cadastrado", "Este e-mail já está cadastrado.") from None

    criar_categorias_iniciais(db, usuario.id)
    token = criar_sessao(db, usuario, agora)
    db.commit()
    return usuario, token


def entrar(db: Session, email_informado: str, senha: str, agora: datetime) -> tuple[Usuario, str]:
    """Login com e-mail e senha. Nunca revela se o e-mail existe."""
    email = email_informado.strip().lower()[:MAX_EMAIL]
    db.execute(delete(TentativaLogin).where(TentativaLogin.ocorrida_em < agora - RETENCAO_FALHAS))

    falhas = db.scalars(
        select(TentativaLogin.ocorrida_em).where(TentativaLogin.email_normalizado == email)
    ).all()
    bloqueado_ate = calcular_bloqueio(list(falhas), agora)
    if bloqueado_ate is not None:
        db.commit()
        segundos = math.ceil((bloqueado_ate - agora).total_seconds())
        raise ErroApi(
            429,
            "login_bloqueado",
            "Muitas tentativas. Tente de novo mais tarde.",
            headers={"Retry-After": str(segundos)},
        )

    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    # Com e-mail inexistente, verifica contra um hash fictício para gastar o mesmo tempo.
    senha_confere = verificar_senha(usuario.senha_hash if usuario else HASH_FICTICIO, senha)
    if usuario is None or not senha_confere:
        db.add(TentativaLogin(email_normalizado=email, ocorrida_em=agora))
        db.commit()
        raise ErroApi(401, "credenciais_invalidas", "E-mail ou senha inválidos.")

    db.execute(delete(TentativaLogin).where(TentativaLogin.email_normalizado == email))
    if not usuario.ativo:
        # Só depois da senha conferir, para não revelar a situação de contas alheias.
        db.commit()
        raise ErroApi(
            403, "conta_desativada", "Esta conta está desativada. Fale com o administrador."
        )
    # O hash do administrador é o do .env; regravá-lo derrubaria as sessões no próximo início.
    if usuario.papel != PAPEL_ADMIN and precisa_rehash(usuario.senha_hash):
        usuario.senha_hash = hash_senha(senha)
    token = criar_sessao(db, usuario, agora)
    db.commit()
    return usuario, token


def sair(db: Session, sessao: Sessao) -> None:
    encerrar_sessao(db, sessao)
    db.commit()


def trocar_senha(
    db: Session,
    usuario: Usuario,
    sessao_atual: Sessao,
    senha_atual: str,
    nova_senha: str,
    agora: datetime,
) -> None:
    """Troca a senha, conclui a troca obrigatória e derruba as outras sessões."""
    checar_conta_editavel(usuario)
    if not verificar_senha(usuario.senha_hash, senha_atual):
        raise ErroApi(400, "senha_atual_incorreta", "Senha atual incorreta.")
    if nova_senha == senha_atual:
        raise ErroApi(
            422,
            "validacao",
            MENSAGEM_VALIDACAO,
            campos={"nova_senha": "A nova senha deve ser diferente da atual."},
        )
    usuario.senha_hash = hash_senha(nova_senha)
    usuario.troca_senha_obrigatoria = False
    usuario.atualizado_em = agora
    encerrar_outras_sessoes(db, usuario.id, sessao_atual.id)
    db.commit()
