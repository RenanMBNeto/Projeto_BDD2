from app import create_app, db
from app.models import Assessor, Cliente, ProdutoFinanceiro, Produto_Acao, Conta, Portfolio, HistoricoPreco, \
    AuditoriaCompliance
from datetime import date
from decimal import Decimal

app = create_app()


def seed():
    with app.app_context():
        print("--- A criar tabelas e popular o Banco de Dados... ---")

        # Cria as tabelas se não existirem (para o SQLite)
        db.create_all()

        # 1. Criar Assessor (Para Login)
        if not Assessor.query.filter_by(Email='assessor@teste.com').first():
            assessor = Assessor(
                Nome='Assessor Principal',
                Email='assessor@teste.com',
                Nivel='Senior'
            )
            assessor.set_password('senha123')  # Senha: senha123
            db.session.add(assessor)
            print("✅ Criado: Assessor (assessor@teste.com)")

        db.session.commit()

        # Recuperar o assessor
        assessor = Assessor.query.filter_by(Email='assessor@teste.com').first()

        # 2. Criar Cliente (Para Login)
        if not Cliente.query.filter_by(Email='cliente@teste.com').first():
            cliente = Cliente(
                AssessorID=assessor.AssessorID,
                CPF_CNPJ='12345678900',
                NomeCompleto='Cliente Investidor',
                Email='cliente@teste.com',
                StatusCompliance='Aprovado'
            )
            cliente.set_password('senha123')  # Senha: senha123
            db.session.add(cliente)
            db.session.flush()

            # Criar Conta e Portfolio
            conta = Conta(ClienteID=cliente.ClienteID, Agencia='0001', NumeroConta='12345-6', Saldo=100000.00)
            portfolio = Portfolio(ClienteID=cliente.ClienteID, NomePortfolio='Carteira Principal')
            db.session.add(conta)
            db.session.add(portfolio)

            print("✅ Criado: Cliente (cliente@teste.com)")

        # 3. Criar Produtos (Para o Dashboard)
        if not ProdutoFinanceiro.query.filter_by(Ticker='PETR4').first():
            petr4 = Produto_Acao(
                Ticker='PETR4',
                NomeProduto='Petrobras PN',
                ClasseAtivo='Acao',
                NivelRiscoProduto=4,
                Emissor='Petrobras',
                CNPJ_Empresa='33000167000101'
            )
            db.session.add(petr4)
            print("✅ Criado: Produto PETR4")

        db.session.commit()

        # 4. Criar Preço (Para aparecer no gráfico/tabela)
        prod = ProdutoFinanceiro.query.filter_by(Ticker='PETR4').first()
        if prod:
            # Verifica se já existe preço hoje
            existe_preco = HistoricoPreco.query.filter_by(ProdutoID=prod.ProdutoID, Data=date.today()).first()
            if not existe_preco:
                preco = HistoricoPreco(ProdutoID=prod.ProdutoID, Data=date.today(), PrecoFechamento=35.50)
                db.session.add(preco)
                print("✅ Preço do PETR4 atualizado.")

        db.session.commit()
        print("--- \nSUCESSO! O banco de dados está pronto para uso. ---")


if __name__ == '__main__':
    seed()