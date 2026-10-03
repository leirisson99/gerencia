"""carteiras PF e PJ: carteira em lançamentos e recorrências, tem_pj e retiradas

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixos nesta revisão: um tipo novo pede migração nova.
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
    "retirada_feita",
    "retirada_editada",
    "retirada_excluida",
)
TIPOS_EVENTO_0017 = (
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


def _check_tipos(tipos: tuple[str, ...]) -> str:
    return f"tipo IN ({', '.join(repr(t) for t in tipos)})"


def upgrade() -> None:
    op.add_column(
        "usuario", sa.Column("tem_pj", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    for tabela in ("lancamento", "recorrencia"):
        op.add_column(
            tabela, sa.Column("carteira", sa.String(2), server_default="pf", nullable=False)
        )
        op.create_check_constraint(f"ck_{tabela}_carteira", tabela, "carteira IN ('pf', 'pj')")
    op.drop_index("ix_lancamento_usuario_data", table_name="lancamento")
    op.create_index(
        "ix_lancamento_usuario_carteira_data", "lancamento", ["usuario_id", "carteira", "data"]
    )

    op.create_table(
        "retirada",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.BigInteger(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("valor", sa.BigInteger(), nullable=False),
        sa.Column("descricao", sa.String(200)),
        sa.Column(
            "lancamento_pj_id",
            sa.BigInteger(),
            sa.ForeignKey("lancamento.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "lancamento_pf_id",
            sa.BigInteger(),
            sa.ForeignKey("lancamento.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("valor > 0", name="ck_retirada_valor_positivo"),
        sa.UniqueConstraint("lancamento_pj_id", name="uq_retirada_lancamento_pj_id"),
        sa.UniqueConstraint("lancamento_pf_id", name="uq_retirada_lancamento_pf_id"),
    )
    op.create_index("ix_retirada_usuario_id", "retirada", ["usuario_id"])

    op.drop_constraint("ck_evento_uso_tipo", "evento_uso", type_="check")
    op.create_check_constraint("ck_evento_uso_tipo", "evento_uso", _check_tipos(TIPOS_EVENTO))


def downgrade() -> None:
    conexao = op.get_bind()
    tem_pj = conexao.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM lancamento WHERE carteira = 'pj')"
            " OR EXISTS (SELECT 1 FROM recorrencia WHERE carteira = 'pj')"
            " OR EXISTS (SELECT 1 FROM retirada)"
        )
    )
    if tem_pj:
        raise RuntimeError("Há dados na carteira PJ: o downgrade da 0018 apagaria dinheiro.")

    op.execute("DELETE FROM evento_uso WHERE tipo LIKE 'retirada_%'")
    op.drop_constraint("ck_evento_uso_tipo", "evento_uso", type_="check")
    op.create_check_constraint("ck_evento_uso_tipo", "evento_uso", _check_tipos(TIPOS_EVENTO_0017))
    op.drop_table("retirada")
    op.drop_index("ix_lancamento_usuario_carteira_data", table_name="lancamento")
    op.create_index("ix_lancamento_usuario_data", "lancamento", ["usuario_id", "data"])
    for tabela in ("lancamento", "recorrencia"):
        op.drop_constraint(f"ck_{tabela}_carteira", tabela, type_="check")
        op.drop_column(tabela, "carteira")
    op.drop_column("usuario", "tem_pj")
