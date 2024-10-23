from src.lib.coinos import Coinos
from src.configs import COINOS_PASSWORD, COINOS_USERNAME

coinos = Coinos()
coinos.login(
    COINOS_USERNAME,
    COINOS_PASSWORD
)
