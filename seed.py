"""Insere registos fictícios na base local (dados.db) para demonstrar o painel.

Uso: python seed.py [quantidade]
"""

import random
import sys
from datetime import date, time, timedelta

from db import obter_repo
from validacao import validar

OPERADORES = ["Ana", "João", "Marta", "Pedro", "Rui"]
PESO_OPERADOR = [1, 3, 1.5, 1, 2]
HORAS = list(range(7, 20))
PESO_HORA = [1, 1, 2, 3, 5, 5, 2, 1, 2, 3, 5, 3, 1]  # picos às 11–12h e às 17h
PRODUTOS = ["REF-1001", "REF-1002", "REF-2040", "REF-3310", "REF-4500", None]


def main(n: int = 100) -> None:
    repo = obter_repo({})
    hoje = date.today()
    for i in range(n):
        repo.inserir(validar({
            "data": hoje - timedelta(days=random.randint(0, 29)),
            "numero_encomenda": f"ENC-{10000 + i}",
            "operador": random.choices(OPERADORES, PESO_OPERADOR)[0],
            "hora_picking": time(random.choices(HORAS, PESO_HORA)[0], random.randint(0, 59)),
            "tipo_erro": random.choices(["Troca", "Falta", "Excesso"], [3, 5, 2])[0],
            "produto": random.choice(PRODUTOS),
            "quantidade": random.choice([None, 1, 1, 2, 3]),
            "observacao": None,
        }))
    print(f"{n} registos de exemplo inseridos em dados.db")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
