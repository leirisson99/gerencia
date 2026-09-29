from datetime import date

from sqlalchemy.orm import Session

from app.domain.saldo import Movimento, resumir
from app.schemas.ciclo import CicloOut
from app.schemas.resumo import ResumoCicloOut, TotalCategoriaOut
from app.services.ciclo import lancamentos_no_ciclo, obter_ciclo_da_data


def resumo_do_ciclo(db: Session, usuario_id: int, data: date) -> ResumoCicloOut:
    ciclo = obter_ciclo_da_data(db, usuario_id, data)
    lancamentos = lancamentos_no_ciclo(db, usuario_id, ciclo)
    resumo = resumir(
        Movimento(lanc.categoria_id, lanc.tipo, lanc.valor, lanc.status, lanc.conta_no_saldo)
        for lanc in lancamentos
    )

    # Categoria (mesmo inativa) de cada lançamento; o tipo vem do lançamento.
    categorias = {lanc.categoria_id: (lanc.categoria.nome, lanc.tipo) for lanc in lancamentos}

    def por_tipo(tipo: str) -> list[TotalCategoriaOut]:
        itens = [
            TotalCategoriaOut(categoria_id=cid, nome=categorias[cid][0], total=total)
            for cid, total in resumo.por_categoria.items()
            if categorias[cid][1] == tipo
        ]
        return sorted(itens, key=lambda item: (-item.total, item.nome))

    return ResumoCicloOut(
        ciclo=CicloOut.model_validate(ciclo),
        entradas=resumo.entradas,
        saidas=resumo.saidas,
        saldo=resumo.saldo,
        saidas_por_categoria=por_tipo("saida"),
        entradas_por_categoria=por_tipo("entrada"),
    )
