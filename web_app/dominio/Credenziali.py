class Credenziali:

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

    def check_password(self, inserita: str) -> bool:
        return self.password == inserita
