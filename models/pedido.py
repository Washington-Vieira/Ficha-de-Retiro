from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Pedido:
    serial: str
    maquina: str
    posto: str
    coordenada: str
    modelo: str
    ot: str
    semiacabado: str
    pagoda: str
    status: str = "PENDENTE"
    data_criacao: datetime = datetime.now()
    data_atualizacao: Optional[datetime] = None
    responsavel_separacao: Optional[str] = None
    data_separacao: Optional[datetime] = None
    responsavel_coleta: Optional[str] = None
    data_coleta: Optional[datetime] = None

    @staticmethod
    def status_validos():
        return ['PENDENTE', 'PROCESSO', 'CONCLUÍDO']

    def atualizar_status(self, novo_status: str):
        novo_status = novo_status.upper()
        if novo_status not in self.status_validos():
            raise ValueError(f"Status inválido. Status permitidos: {self.status_validos()}")
        self.status = novo_status
        self.data_atualizacao = datetime.now()