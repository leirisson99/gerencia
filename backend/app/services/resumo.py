from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.limite import situacao
from app.domain.saldo import Movimento, resumir
from app.models import Categoria
from app.schemas.ciclo import CicloOut
from app.schemas.resumo import ResumoCicloOut, TotalCategoriaOut
from app.services.ciclo import lancamentos_no_ciclo, obter_ciclo_da_data


def _item(categoria_id: int, nome: str, total: int, limite: int | None) -> TotalCategoriaOut:
    return TotalCategoriaOut(
        categoria_id=categoria_id,
        nome=nome,
        total=total,
        limite=limite,
        situacao=situacao(total, limite) if limite is not None else None,
    )


def resumo_do_ciclo(db: Session, usuario_id: int, data: date) -> ResumoCicloOut:
    ciclo = obter_ciclo_da_data(db, usuario_id, data)
    lancamentos = lancamentos_no_ciclo(db, usuario_id, ciclo)
    resumo = resumir(
        Movimento(lanc.categoria_id, lanc.tipo, lanc.valor, lanc.status, lanc.conta_no_saldo)
        for lanc in lancamentos
    )

    # Categoria (mesmo inativa) de cada lançamento; o tipo vem do lançamento.
    categorias = {lanc.categoria_id: lanc.categoria for lanc in lancamentos}
    tipos = {lanc.categoria_id: lanc.tipo for lanc in lancamentos}

    def por_tipo(tipo: str) -> list[TotalCategoriaOut]:
        itens = [
            _item(
                cid,
                categorias[cid].nome,
                total,
                categorias[cid].limite if tipo == "saida" else None,
            )
            for cid, total in resumo.por_categoria.items()
            if tipos[cid] == tipo
        ]
        return sorted(itens, key=lambda item: (-item.total, item.nome))

    # Categorias ativas com limite e sem gasto no ciclo entram zeradas, depois das com gasto.
    sem_gasto = db.scalars(
        select(Categoria)
        .where(
            Categoria.usuario_id == usuario_id,
            Categoria.tipo == "saida",
            Categoria.ativa,
            Categoria.limite.is_not(None),
            Categoria.id.not_in(resumo.por_categoria.keys()),
        )
        .order_by(Categoria.nome)
    )

    return ResumoCicloOut(
        ciclo=CicloOut.model_validate(ciclo),
        entradas=resumo.entradas,
        saidas=resumo.saidas,
        saldo=resumo.saldo,
        saidas_por_categoria=por_tipo("saida")
        + [_item(c.id, c.nome, 0, c.limite) for c in sem_gasto],
        entradas_por_categoria=por_tipo("entrada"),
    )
