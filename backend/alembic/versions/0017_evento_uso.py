"""eventos de uso e a ação ver_atividade, para o detalhe da conta no painel do administrador

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixa nesta revisão: um tipo novo pede migração nova.
TIPOS_EVENTO = (
    "conta_criada",
    "login",
    "senha_trocada",
    "perfil_atualizado",
    "lancamento_criado",
    "lancamento_editado",
    "lancamento_excluido",
    "extrato_importado",
    "categoria_criada",
    "categoria_editada",
    "recorrencia_criada",
    "recorrencia_editada",
    "divida_criada",
    "cartela_criada",
    "deposito_feito",
    "deposito_desfeito",
    "servico_criado",
    "servico_editado",
    "servico_excluido",
    "servico_recebido",
    "recebimento_desfeito",
    "lembrete_criado",
    "lembrete_editado",
    "lembrete_concluido",
    "lembrete_excluido",
    "push_ativado",
    "push_removido",
)


def upgrade() -> None:
    op.create_table(
        "evento_uso",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.BigInteger(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column(
            "ocorrido_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"tipo IN ({', '.join(repr(t) for t in TIPOS_EVENTO)})", name="ck_evento_uso_tipo"
        ),
    )
    op.create_index("ix_evento_uso_usuario_id_id", "evento_uso", ["usuario_id", "id"])
    op.create_index("ix_evento_uso_ocorrido_em", "evento_uso", ["ocorrido_em"])

    op.drop_constraint("ck_acao_admin_acao", "acao_admin", type_="check")
    op.create_check_constraint(
        "ck_acao_admin_acao",
        "acao_admin",
        "acao IN ('reset_senha', 'desativar_conta', 'reativar_conta', 'ver_atividade')",
    )


def downgrade() -> None:
    op.execute("DELETE FROM acao_admin WHERE acao = 'ver_atividade'")
    op.drop_constraint("ck_acao_admin_acao", "acao_admin", type_="check")
    op.create_check_constraint(
        "ck_acao_admin_acao",
        "acao_admin",
        "acao IN ('reset_senha', 'desativar_conta', 'reativar_conta')",
    )
    op.drop_table("evento_uso")
