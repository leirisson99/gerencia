"""Contas de demonstração para gravar os vídeos de cada feature.

Tudo passa pela API, como se alguém usasse o app: as regras de ciclo, parcelas,
recorrências e cartela valem para estes dados como para qualquer outro.
As datas são relativas a "hoje", para que o ciclo atual sempre tenha o que mostrar.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any

# (método, caminho, corpo) -> (status, json); cada conta usa a própria sessão.
Chamada = Callable[[str, str, object], tuple[int, Any]]

DIA_SALARIO = 5
SALARIO = 350_000
CICLOS = 3


class ErroDemo(Exception):
    """A API recusou um passo da carga; a mensagem diz qual."""


@dataclass(frozen=True)
class Conta:
    nome: str
    email: str
    telefone: str
    cargo: str
    tipo_renda: str

    def com_sufixo(self, sufixo: str) -> "Conta":
        """Outra conta igual (ana.demo+v04@...), para gravar de novo a partir do zero."""
        usuario, dominio = self.email.split("@")
        return replace(self, email=f"{usuario}+{sufixo}@{dominio}")


ANA = Conta("Ana Souza", "ana.demo@exemplo.com", "11987654321", "Analista administrativa", "clt")
CARLOS = Conta(
    "Carlos Lima", "carlos.demo@exemplo.com", "21987654321", "Designer freelancer", "prestador"
)

# (dias depois do início do ciclo, categoria, valor em centavos, descrição)
GASTOS_DO_CICLO: tuple[tuple[int, str, int, str], ...] = (
    (1, "Alimentação", 48_000, "Mercado do mês"),
    (3, "Transporte", 3_500, "Uber"),
    (6, "Lazer", 6_000, "Cinema"),
    (8, "Alimentação", 9_500, "Restaurante"),
    (11, "Saúde", 7_800, "Farmácia"),
    (13, "Lazer", 8_000, "Bar com amigos"),
    (15, "Alimentação", 21_000, "Feira e açougue"),
    (18, "Lazer", 12_000, "Show"),
    (20, "Transporte", 25_000, "Combustível"),
    (24, "Outros", 6_900, "Presente de aniversário"),
)


def _chamar(api: Chamada, metodo: str, caminho: str, corpo: object = None) -> Any:
    status, resposta = api(metodo, caminho, corpo)
    if status >= 400:
        raise ErroDemo(f"{metodo} {caminho} recusado ({status}): {resposta}")
    return resposta


def datas_de_salario(hoje: date, dia: int = DIA_SALARIO, quantidade: int = CICLOS) -> list[date]:
    """As últimas `quantidade` datas com aquele dia do mês até hoje, da mais antiga à mais nova."""
    ano, mes = hoje.year, hoje.month
    if hoje.day < dia:
        ano, mes = (ano - 1, 12) if mes == 1 else (ano, mes - 1)
    datas = []
    for _ in range(quantidade):
        datas.append(date(ano, mes, dia))
        ano, mes = (ano - 1, 12) if mes == 1 else (ano, mes - 1)
    return sorted(datas)


def _mes_anterior(inicio_do_mes: date) -> date:
    return (inicio_do_mes - timedelta(days=1)).replace(day=1)


def _cadastrar(api: Chamada, conta: Conta, senha: str) -> bool:
    """Cria a conta (o cadastro já deixa a sessão aberta). False se o e-mail já existe."""
    status, resposta = api(
        "POST",
        "/api/v1/auth/cadastro",
        {
            "nome": conta.nome,
            "email": conta.email,
            "telefone": conta.telefone,
            "cargo": conta.cargo,
            "senha": senha,
            "tipo_renda": conta.tipo_renda,
        },
    )
    if status == 409:
        return False
    if status >= 400:
        raise ErroDemo(f"cadastro de {conta.email} recusado ({status}): {resposta}")
    return True


def _categorias(api: Chamada) -> dict[str, int]:
    return {c["nome"]: c["id"] for c in _chamar(api, "GET", "/api/v1/categorias")}


def _lancar(
    api: Chamada,
    categoria_id: int,
    valor: int,
    data: date,
    descricao: str,
    status: str = "realizado",
) -> dict[str, Any]:
    return _chamar(
        api,
        "POST",
        "/api/v1/lancamentos",
        {
            "categoria_id": categoria_id,
            "valor": valor,
            "data": data.isoformat(),
            "descricao": descricao,
            "status": status,
        },
    )


def _confirmar(api: Chamada, lancamento_id: int) -> None:
    _chamar(api, "PATCH", f"/api/v1/lancamentos/{lancamento_id}", {"status": "realizado"})


def popular_ana(api: Chamada, hoje: date, senha: str, conta: Conta = ANA) -> bool:
    """CLT: três ciclos de salário, fixos, limites, dívidas, cartela e contas a vencer."""
    if not _cadastrar(api, conta, senha):
        return False
    cat = _categorias(api)

    # Lazer fica perto do limite no ciclo atual: o próximo gasto de lazer dispara o aviso.
    _chamar(api, "PATCH", f"/api/v1/categorias/{cat['Lazer']}", {"limite": 30_000})
    _chamar(api, "PATCH", f"/api/v1/categorias/{cat['Alimentação']}", {"limite": 90_000})

    # Recorrências antes dos salários: cada ciclo que abre já gera os previstos.
    for descricao, categoria, valor, dia in (
        ("Aluguel", "Moradia", 120_000, 10),
        ("Internet", "Moradia", 10_000, 15),
        ("Academia", "Saúde", 9_000, 20),
    ):
        _chamar(
            api,
            "POST",
            "/api/v1/recorrencias",
            {"descricao": descricao, "categoria_id": cat[categoria], "valor": valor, "dia": dia},
        )

    salarios = datas_de_salario(hoje)
    for data in salarios:
        _lancar(api, cat["Salário"], SALARIO, data, "Salário")

    fins = [proximo - timedelta(days=1) for proximo in salarios[1:]] + [hoje]
    for inicio, fim in zip(salarios, fins, strict=True):
        for dias, categoria, valor, descricao in GASTOS_DO_CICLO:
            data = inicio + timedelta(days=dias)
            if data <= fim:
                _lancar(api, cat[categoria], valor, data, descricao)

        # Fixos pagos; no ciclo atual o aluguel fica em aberto (atrasado nos lembretes,
        # e o vídeo de recorrências confirma o pagamento ao vivo).
        atual = inicio == salarios[-1]
        for lancamento in _chamar(api, "GET", f"/api/v1/ciclos/{inicio.isoformat()}/lancamentos"):
            if (
                lancamento["recorrencia_id"] is not None
                and lancamento["status"] == "previsto"
                and date.fromisoformat(lancamento["data"]) <= hoje
                and not (atual and lancamento["descricao"] == "Aluguel")
            ):
                _confirmar(api, lancamento["id"])

    _lancar(api, cat["Renda extra"], 45_000, salarios[-1] + timedelta(days=2), "Freela de design")
    _lancar(api, cat["Moradia"], 18_000, hoje + timedelta(days=2), "Conta de luz", "previsto")

    # Dívidas: parcelas vencidas até hoje ficam pagas ou recebidas.
    for dados in (
        {
            "descricao": "Celular novo",
            "pessoa": "Loja de eletrônicos",
            "direcao": "devo",
            "valor_total": 240_000,
            "parcelas": 10,
            "forma_pagamento": "cartao",
            "dia_vencimento": 10,
            "data_inicio": salarios[0].isoformat(),
            "categoria_id": cat["Outros"],
        },
        {
            "descricao": "Empréstimo",
            "pessoa": "João",
            "direcao": "me_devem",
            "valor_total": 60_000,
            "parcelas": 3,
            "forma_pagamento": "pix",
            "dia_vencimento": 25,
            "data_inicio": salarios[1].isoformat(),
            "categoria_id": cat["Renda extra"],
        },
    ):
        divida = _chamar(api, "POST", "/api/v1/dividas", dados)
        for parcela in divida["lancamentos"]:
            if date.fromisoformat(parcela["data"]) < hoje:
                _confirmar(api, parcela["id"])

    cartela = _chamar(
        api,
        "POST",
        "/api/v1/cartelas",
        {"nome": "Reserva de emergência", "meta": 500_000, "valor_base": 1_000},
    )
    for casa in sorted(cartela["casas"], key=lambda c: c["ordem"])[:8]:
        _chamar(api, "POST", f"/api/v1/cartelas/{cartela['id']}/casas/{casa['id']}/deposito")
    return True


def popular_carlos(api: Chamada, hoje: date, senha: str, conta: Conta = CARLOS) -> bool:
    """Prestador: ciclo pelo mês, serviços recebidos, atrasado e a receber."""
    if not _cadastrar(api, conta, senha):
        return False
    _chamar(api, "POST", "/api/v1/categorias", {"nome": "Serviços", "tipo": "entrada"})
    cat = _categorias(api)

    for descricao, categoria, valor, dia in (
        ("Coworking", "Moradia", 45_000, 5),
        ("Assinatura de software", "Outros", 8_000, 12),
    ):
        _chamar(
            api,
            "POST",
            "/api/v1/recorrencias",
            {"descricao": descricao, "categoria_id": cat[categoria], "valor": valor, "dia": dia},
        )

    mes_atual = hoje.replace(day=1)
    meses = [_mes_anterior(_mes_anterior(mes_atual)), _mes_anterior(mes_atual), mes_atual]
    for inicio in meses:
        for dias, categoria, valor, descricao in GASTOS_DO_CICLO[::2]:
            data = inicio + timedelta(days=dias)
            if data <= hoje and data.month == inicio.month:
                _lancar(api, cat[categoria], valor, data, descricao)

    # (cliente, descrição, valor, data prevista, recebido)
    servicos = (
        ("Loja da Maria", "Identidade visual", 80_000, meses[0] + timedelta(days=14), True),
        ("Padaria Pão Quente", "Cardápio", 35_000, meses[1] + timedelta(days=9), True),
        ("Clínica Sorriso", "Site institucional", 150_000, meses[1] + timedelta(days=24), True),
        ("Academia Forma", "Posts do mês", 60_000, hoje - timedelta(days=5), False),
        ("Loja da Maria", "Banner da promoção", 25_000, hoje + timedelta(days=2), False),
        ("Escritório Lima", "Logotipo", 90_000, hoje + timedelta(days=12), False),
    )
    for cliente, descricao, valor, prevista, recebido in servicos:
        servico = _chamar(
            api,
            "POST",
            "/api/v1/servicos",
            {
                "cliente": cliente,
                "descricao": descricao,
                "valor": valor,
                "data_prevista": prevista.isoformat(),
                "categoria_id": cat["Serviços"],
            },
        )
        if recebido:
            _chamar(
                api,
                "POST",
                f"/api/v1/servicos/{servico['id']}/recebimento",
                {"data": prevista.isoformat()},
            )
    return True


Popular = Callable[[Chamada, date, str, Conta], bool]

PERSONAS: dict[str, tuple[Conta, Popular]] = {
    "ana": (ANA, popular_ana),
    "carlos": (CARLOS, popular_carlos),
}
