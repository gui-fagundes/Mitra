from sqlalchemy import inspect


class SerializavelMixin:
    def para_dict(self, incluir_nulos: bool = False) -> dict:
        dados = {}

        for coluna in inspect(self).mapper.column_attrs:
            valor = getattr(self, coluna.key)
            if incluir_nulos or valor is not None:
                dados[coluna.key] = valor

        for relacao in inspect(self).mapper.relationships:
            relacionado = getattr(self, relacao.key)
            if relacionado is not None:
                if isinstance(relacionado, list):
                    dados[relacao.key] = [r.para_dict(incluir_nulos) for r in relacionado]
                else:
                    dados[relacao.key] = relacionado.para_dict(incluir_nulos)

        return dados
