from pathlib import Path
import sys

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ_PROJETO))

from sqlalchemy import create_engine, text
from config import POSTGRES_URL

engine = create_engine(POSTGRES_URL)

with engine.connect() as conexao:
    print(conexao.execute(text("SELECT 1")).scalar())
