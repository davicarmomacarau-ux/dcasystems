import re
from decimal import Decimal

# Módulo de parsing de legado inspirado em conversores mainframe e em um sistema Oracle Legacy.
# A ideia é transformar uma string de largura fixa em payload JSON legível para a API moderna.


def parse_legacy_sample(dados_legados: str) -> dict:
    """Recebe uma string de largura fixa estilo mainframe e devolve um dicionário JSON pronto.

    O formato simulado é:
    001JOAO SILVA                   joao.silva@oraclebank.com       00000000012345A
    onde o status é identificado pelo caractere final A ou I.
    """
    try:
        if not isinstance(dados_legados, str) or not dados_legados.strip():
            raise ValueError("A string de dados legados está vazia ou inválida.")

        texto = dados_legados.strip()
        email_match = re.search(r"[\w\.+-]+@[\w\.-]+\.[A-Za-z]{2,}", texto)
        if not email_match:
            raise ValueError("Formato legado sem e-mail reconhecível.")

        email = email_match.group(0)

        # O bloco anterior ao e-mail traz o cliente, com o prefixo tipo Oracle Legacy na frente.
        prefixo = texto[: email_match.start()].strip()
        prefixo = re.sub(r"^\d{3}", "", prefixo).strip()
        # Remove espaços múltiplos para expressar o nome como um único texto legível.
        cliente = re.sub(r"\s+", " ", prefixo)

        # O último bloco traz o saldo com 14 dígitos e o status com A ou I.
        saldo_match = re.search(r"(\d{5,14})([AI])\s*$", texto, re.IGNORECASE)
        if not saldo_match:
            # Fallback para quando o saldo vier com preenchimento de zeros após o e-mail e o status por fim.
            saldo_match = re.search(r"(\d{14})([AI])$", texto, re.IGNORECASE)

        if not saldo_match:
            raise ValueError("Formato legado sem saldo e status reconhecíveis.")

        saldo_inteiro = saldo_match.group(1)
        status_codigo = saldo_match.group(2).upper()

        saldo_decimal = Decimal(saldo_inteiro) / Decimal("100")
        status = "ativo" if status_codigo == "A" else "inativo"

        # Resposta final do parser no formato solicitado: campo saldo em decimal e status interpretado.
        return {
            "cliente": cliente,
            "email": email,
            "saldo": f"{saldo_decimal:.2f}",
            "status": status,
            "canal_origem": "oracle-legacy-mainframe",
            "tipo": "migracao-amostra",
        }
    except Exception as erro:
        # Tratamento de exceção em parser para evitar travar a API por formato ruim.
        raise ValueError(f"Formato legado inválido: {erro}") from erro
