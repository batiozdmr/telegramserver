import sqlite3

# Veritabanına bağlan
conn = sqlite3.connect('halka_arz.db')
cursor = conn.cursor()

# Filtrelemek istediğiniz tarih
hedef_tarih = '13 Ekim 2023'

# SQL sorgusu
sorgu = """
SELECT *
FROM halka_arz
WHERE offering_start_date <= ? AND offering_finish_date >= ?
"""

# Sorguyu çalıştır
cursor.execute(sorgu, (hedef_tarih, hedef_tarih))

# Sonuçları al
sonuclar = cursor.fetchall()

# Sonuçları yazdır
for sonuc in sonuclar:
    print(sonuc)

# Bağlantıyı kapat
conn.close()