"""Exemplo embutido, usado quando nenhum arquivo é informado na CLI."""

# Parada de manutenção de uma válvula.
PARADA_VALVULA = """id,nome,duracao,predecessoras
A,Liberação da área (PT),1,
B,Montagem de andaime,3,A
C,Raquetamento da linha,2,A
D,Desmontagem da válvula,2,B;C
E,Inspeção do flange,1,C
F,Montagem da válvula nova,2,D;E
G,Teste e liberação,1,F
"""
