"""Extração de texto de PDF (infraestrutura). O layout de cada banco é lido em `domain/extrato`."""

import io
import logging

import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from pdfplumber.utils.exceptions import MalformedPDFException, PdfminerException

from app.domain.extrato import ErroExtrato, LinhaPdf

# pdfminer registra avisos de fonte a cada página; não ajudam e podem poluir o log.
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class PdfSemTexto(ErroExtrato):
    """PDF sem texto extraível (escaneado ou imagem)."""


def linhas_do_pdf(conteudo: bytes) -> list[LinhaPdf]:
    try:
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            linhas = [
                LinhaPdf(numero, float(linha["top"]), float(linha["x0"]), linha["text"])
                for numero, pagina in enumerate(pdf.pages, start=1)
                for linha in pagina.extract_text_lines()
            ]
    except (
        PDFSyntaxError,
        PdfminerException,
        MalformedPDFException,
        ValueError,
        KeyError,
        TypeError,
    ) as erro:
        raise ErroExtrato("O arquivo não é um PDF válido.") from erro
    if not any(linha.texto.strip() for linha in linhas):
        raise PdfSemTexto("O PDF não tem texto. Envie o PDF gerado pelo banco, não uma foto.")
    return linhas
