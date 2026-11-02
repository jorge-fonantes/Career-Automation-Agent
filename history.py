import sqlite3
from datetime import datetime, timezone

from job_filter import chave_vaga

class JobHistory:
    """ Lembra as vagas já enviadas, para o relatório trazer só novidades. """

    def __init__(self, caminho):
        self.conn = sqlite3.connect(caminho)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vagas_vistas (
                chave TEXT PRIMARY KEY,
                titulo TEXT,
                empresa TEXT,
                url TEXT,
                enviada_em TEXT
            )
        """)

    def novas(self, vagas):
        return [j for j in vagas if not self.conn.execute(
            "SELECT 1 FROM vagas_vistas WHERE chave = ?", (chave_vaga(j),)
        ).fetchone()]

    def marcar_enviadas(self, vagas):
        agora = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.executemany(
                "INSERT OR IGNORE INTO vagas_vistas VALUES (?, ?, ?, ?, ?)",
                [(chave_vaga(j), j.title, j.company, j.url, agora) for j in vagas],
            )

    def close(self):
        self.conn.close()
