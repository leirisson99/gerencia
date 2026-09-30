"""Bancos suportados e o leitor de cada formato. Banco novo: leitor testado + entrada aqui."""

from collections.abc import Callable
from dataclasses import dataclass

from app.domain.extrato import Formato, LinhaExtrato, LinhaPdf
from app.domain.extrato.csv import ler_csv_inter, ler_csv_nubank
from app.domain.extrato.ofx import ler_ofx
from app.domain.extrato.pdf import (
    ler_pdf_inter,
    ler_pdf_itau,
    ler_pdf_mercado_pago,
    ler_pdf_neon,
    ler_pdf_nubank,
)

LeitorTexto = Callable[[str], list[LinhaExtrato]]
LeitorPdf = Callable[[list[LinhaPdf]], list[LinhaExtrato]]


@dataclass(frozen=True)
class Banco:
    codigo: str
    nome: str
    texto: dict[Formato, LeitorTexto]  # ofx e csv com layout do banco
    pdf: LeitorPdf | None = None
    csv_generico: bool = False  # colunas informadas pelo usuário

    @property
    def formatos(self) -> list[Formato]:
        formatos: list[Formato] = list(self.texto)
        if self.pdf is not None:
            formatos.append("pdf")
        if self.csv_generico:
            formatos.append("csv_generico")
        return formatos


OUTRO = "outro"

BANCOS: dict[str, Banco] = {
    banco.codigo: banco
    for banco in (
        Banco("inter", "Inter", {"ofx": ler_ofx, "csv": ler_csv_inter}, ler_pdf_inter),
        Banco("itau", "Itaú", {"ofx": ler_ofx}, ler_pdf_itau),
        Banco("mercado_pago", "Mercado Pago", {}, ler_pdf_mercado_pago),
        Banco("neon", "Neon", {}, ler_pdf_neon),
        Banco("nubank", "Nubank", {"ofx": ler_ofx, "csv": ler_csv_nubank}, ler_pdf_nubank),
        # Qualquer outro banco: OFX padrão ou CSV com as colunas informadas.
        Banco(OUTRO, "Outro banco", {"ofx": ler_ofx}, csv_generico=True),
    )
}
