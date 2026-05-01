import sqlite3

def popular_lojas():
    # Conecta ao arquivo de banco de dados
    conn = sqlite3.connect('cacique_intel.db')
    cursor = conn.cursor()
    
    # 1. DEFINIR A ESTRUTURA (O Blueprint)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Lojas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            zona TEXT,
            lat REAL,
            lon REAL
        )
    ''')
    
    # 2. INSERIR OS DADOS (A Mobília)
    lojas = [
        ("Cacique 01 (Sul)", "Sul", -5.092700, -42.801114),
        ("Cacique 06 (Norte)", "Norte", -5.078611, -42.822128),
        ("Cacique 11 (Sudeste)", "Sudeste", -5.099200, -42.765392),
        ("Cacique Leste (Leste)", "Leste", -5.062598, -42.799236)
    ]
    
    cursor.executemany('INSERT INTO Lojas (nome, zona, lat, lon) VALUES (?, ?, ?, ?)', lojas)
    
    # Salva as alterações
    conn.commit()
    conn.close()
    print("Sucesso! Tabela criada e dados inseridos.")

if __name__ == "__main__":
    popular_lojas()