from app import create_app, db
from app.models import Assessor, Cliente

app = create_app()


def reset_pass():
    with app.app_context():
        print("--- Redefinindo Senhas ---")

        # 1. Atualizar Assessor
        assessor = Assessor.query.filter_by(Email='assessor@teste.com').first()
        if assessor:
            assessor.set_password('senha123')  # Gera o hash correto
            print(f"✅ Senha do Assessor ({assessor.Email}) atualizada para 'senha123'")
        else:
            print("❌ Assessor não encontrado. Crie o usuário primeiro.")

        # 2. Atualizar Cliente
        cliente = Cliente.query.filter_by(Email='cliente@teste.com').first()
        if cliente:
            cliente.set_password('senha123')
            print(f"✅ Senha do Cliente ({cliente.Email}) atualizada para 'senha123'")
        else:
            print("❌ Cliente não encontrado.")

        db.session.commit()
        print("--- Concluído ---")


if __name__ == "__main__":
    reset_pass()