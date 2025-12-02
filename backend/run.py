from app import create_app, db
from app.models import *

app = create_app() 

@app.shell_context_processor
def make_shell_context():
    return {
        'app': app,
        'db': db,
        'Cliente': Cliente,
        'Assessor': Assessor,
        'GrupoEconomico': GrupoEconomico,
        'ClienteGrupoLink': ClienteGrupoLink,
        'AuditoriaCompliance': AuditoriaCompliance,
        'QuestionarioSuitabilityVersao': QuestionarioSuitabilityVersao,
        'Pergunta': Pergunta,
        'OpcaoResposta': OpcaoResposta,
        'RespostaSuitabilityCliente': RespostaSuitabilityCliente,
        'ProdutoFinanceiro': ProdutoFinanceiro,
        'Produto_Acao': Produto_Acao,
        'Produto_RendaFixa': Produto_RendaFixa,
        'Produto_Fundo': Produto_Fundo,
        'HistoricoPreco': HistoricoPreco,
        'ComposicaoFundo': ComposicaoFundo,
        'Conta': Conta,
        'Portfolio': Portfolio,
        'MovimentacaoConta': MovimentacaoConta,
        'Ordem': Ordem,
        'Posicao': Posicao
    }