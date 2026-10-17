"""contas compartilhadas: conta, participante, cobrança mensal e cota

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixos nesta revisão: um tipo novo pede migração nova.
TIPOS_NOVOS = (
    "conta_compartilhada_criada",
    "convite_aceito",
    "convite_recusado",
    "cobranca_gerada",
    "cota_confirmada",
)
TIPOS_EVENTO_0018 = (
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
TIPOS_EVENTO = TIPOS_EVENTO_0018 + TIPOS_NOVOS


def _check_tipos(tipos: tuple[str, ...]) -> str:
    return f"tipo IN ({', '.join(repr(t) for t in tipos)})"


def upgrade() -> None:
    op.create_table(
        "conta_compartilhada",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "dono_id",
            sa.BigInteger(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "categoria_id",
            sa.BigInteger(),
            sa.ForeignKey("categoria.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("descricao", sa.String(200), nullable=False),
        sa.Column("modo", sa.String(10), nullable=False),
        sa.Column("dia_vencimento", sa.SmallInteger(), nullable=False),
        sa.Column("valor_fixo", sa.BigInteger()),
        sa.Column("ativa", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "modo IN ('igual', 'percentual', 'fixo')", name="ck_conta_compartilhada_modo"
        ),
        sa.CheckConstraint(
            "dia_vencimento BETWEEN 1 AND 31", name="ck_conta_compartilhada_dia_vencimento"
        ),
        sa.CheckConstraint(
            "valor_fixo IS NULL OR valor_fixo > 0", name="ck_conta_compartilhada_valor_fixo"
        ),
    )
    op.create_index("ix_conta_compartilhada_dono_id", "conta_compartilhada", ["dono_id"])

    op.create_table(
        "participante_conta",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "conta_id",
            sa.BigInteger(),
            sa.ForeignKey("conta_compartilhada.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("usuario_id", sa.BigInteger(), sa.ForeignKey("usuario.id", ondelete="CASCADE")),
        sa.Column("email_convite", sa.String(254)),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column(
            "categoria_id",
            sa.BigInteger(),
            sa.ForeignKey("categoria.id", ondelete="RESTRICT"),
        ),
        sa.Column("valor", sa.BigInteger()),
        sa.Column("eh_dono", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "convidado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('pendente', 'aceito', 'recusado', 'removido', 'saiu')",
            name="ck_participante_conta_status",
        ),
        sa.CheckConstraint("valor IS NULL OR valor >= 0", name="ck_participante_conta_valor"),
        sa.CheckConstraint(
            "eh_dono OR email_convite IS NOT NULL", name="ck_participante_conta_convite"
        ),
        sa.UniqueConstraint("conta_id", "usuario_id", name="uq_participante_conta_conta_usuario"),
        sa.UniqueConstraint("conta_id", "email_convite", name="uq_participante_conta_conta_email"),
    )
    op.create_index("ix_participante_conta_conta_id", "participante_conta", ["conta_id"])
    op.create_index("ix_participante_conta_usuario_id", "participante_conta", ["usuario_id"])
    op.create_index(
        "uq_participante_conta_dono",
        "participante_conta",
        ["conta_id"],
        unique=True,
        postgresql_where=sa.text("eh_dono"),
    )
    op.create_index(
        "ix_participante_conta_email_pendente",
        "participante_conta",
        ["email_convite"],
        postgresql_where=sa.text("status = 'pendente'"),
    )

    op.create_table(
        "cobranca_mensal",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "conta_id",
            sa.BigInteger(),
            sa.ForeignKey("conta_compartilhada.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("valor_total", sa.BigInteger(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("valor_total > 0", name="ck_cobranca_mensal_valor_total"),
        sa.UniqueConstraint("conta_id", "competencia", name="uq_cobranca_mensal_conta_competencia"),
    )

    op.create_table(
        "cota_cobranca",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "cobranca_id",
            sa.BigInteger(),
            sa.ForeignKey("cobranca_mensal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participante_id",
            sa.BigInteger(),
            sa.ForeignKey("participante_conta.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("valor", sa.BigInteger(), nullable=False),
        sa.Column(
            "lancamento_id",
            sa.BigInteger(),
            sa.ForeignKey("lancamento.id", ondelete="RESTRICT"),
        ),
        sa.Column("confirmado_em", sa.DateTime(timezone=True)),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("valor > 0", name="ck_cota_cobranca_valor_positivo"),
        sa.UniqueConstraint(
            "cobranca_id", "participante_id", name="uq_cota_cobranca_cobranca_participante"
        ),
        sa.UniqueConstraint("lancamento_id", name="uq_cota_cobranca_lancamento_id"),
    )
    op.create_index(
        "ix_cota_cobranca_participante_sem_lancamento",
        "cota_cobranca",
        ["participante_id"],
        postgresql_where=sa.text("lancamento_id IS NULL"),
    )

    op.drop_constraint("ck_evento_uso_tipo", "evento_uso", type_="check")
    op.create_check_constraint("ck_evento_uso_tipo", "evento_uso", _check_tipos(TIPOS_EVENTO))


def downgrade() -> None:
    conexao = op.get_bind()
    tem_cobranca = conexao.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM cobranca_mensal)"))
    if tem_cobranca:
        raise RuntimeError("Há cobranças compartilhadas: o downgrade da 0019 as apagaria.")

    lista = ", ".join(repr(t) for t in TIPOS_NOVOS)
    op.execute(f"DELETE FROM evento_uso WHERE tipo IN ({lista})")
    op.drop_constraint("ck_evento_uso_tipo", "evento_uso", type_="check")
    op.create_check_constraint("ck_evento_uso_tipo", "evento_uso", _check_tipos(TIPOS_EVENTO_0018))
    op.drop_table("cota_cobranca")
    op.drop_table("cobranca_mensal")
    op.drop_table("participante_conta")
    op.drop_table("conta_compartilhada")
