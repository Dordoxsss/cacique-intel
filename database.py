# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('cacique_intel.db')
    cursor = conn.cursor()
    
    # Tabela de lojas (Cadastro)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Lojas (
                        id INTEGER PRIMARY KEY,
                        nome TEXT,
                        zona TEXT,
                        lat REAL,
                        lon REAL)''')
                        
    # Tabela de histórico (Onde a mágica acontece)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Historico (
                        id INTEGER PRIMARY KEY,
                        loja_id INTEGER,
                        data TIMESTAMP,
                        escolas INTEGER,
                        hospitais INTEGER,
                        score REAL,
                        FOREIGN KEY(loja_id) REFERENCES Lojas(id))''')
    
    conn.commit()
    conn.close()

# Dica: Execute init_db() uma única vez no início do seu projeto