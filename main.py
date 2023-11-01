import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import telebot
from bs4 import BeautifulSoup
import sqlite3
from selenium import webdriver
import time

# Tarayıcıyı başlat


# Botunuzun token'ını buraya ekleyin
TOKEN = '6489901128:AAEoNfONPJaJ69w-jW0E0O-4CxzLa1c96S8'
# Botun çalıştığı sohbetin chat_id'sini ayarlayın
CHAT_ID = '-4084637440'
# CHAT_ID = '-4078250422'

# Bot nesnesini oluşturun
bot = telebot.TeleBot(TOKEN)


# Mesaj gönderme fonksiyonu
def send_periodic_message():
    # SQLite veritabanı bağlantısı oluşturun
    conn = sqlite3.connect('halka_arz.db')
    cursor = conn.cursor()
    # Web sitesine GET isteği gönderme
    driver = webdriver.Chrome()
    url = 'https://halkarz.com'
    driver.get(url)
    count_arz = 0
    # Sayfa içeriğini al
    response = driver.page_source
    participation_index = "Uygun Değil"
    response_text = response
    response_status_code = driver.execute_script("return document.readyState")
    # HTTP isteğinin başarılı bir şekilde tamamlanıp tamamlanmadığını kontrol etme
    if response_status_code == "complete":
        # BeautifulSoup ile HTML'i ayrıştırma
        soup = BeautifulSoup(response_text, 'html.parser')

        # <li> elementlerini seçme
        li_elements = soup.find_all('li')
        for li in li_elements:
            il_badge_div = li.find('div', class_='il-badge')
            if il_badge_div:
                il_new_div = il_badge_div.find('div', class_='il-new')
                if il_new_div:
                    company_name = li.find('h3', class_='il-halka-arz-sirket').text.strip()
                    stock_code = li.find('span', class_='il-bist-kod').text.strip()
                    offering_date = li.find('span', class_='il-halka-arz-tarihi').text.strip()
                    web_url = li.find('a').get('href')

                    # "katılım endeksi" ifadesini içeren bir cümle mi kontrol edin
                    participation_index = "Uygun Değil!!!"
                    server = webdriver.Chrome()
                    server.get(web_url)
                    detail_response_text = server.page_source
                    detail_soup = BeautifulSoup(detail_response_text, 'html.parser')
                    for i in range(len(detail_soup)):
                        current_sentence = detail_soup.find('li', class_='b-esit')
                        if current_sentence:
                            if "katılım endeksine uygun" in current_sentence.text.strip().lower():
                                participation_index = "Uygun"
                    # Verinin veritabanında olup olmadığını kontrol et
                    cursor.execute('''SELECT id FROM halka_arz WHERE company_name = ? AND stock_code = ? AND offering_date = ? AND web_url = ?
                        ''', (company_name, stock_code, offering_date, web_url))
                    existing_data = cursor.fetchone()

                    if not existing_data:
                        parcalanmis_veri = offering_date.split('-')
                        tarihler = parcalanmis_veri[:5]
                        ay = tarihler[-1].split(' ')[-2]
                        yil = tarihler[-1].split(' ')[-1]
                        date_count = 0
                        offering_start_date = ""
                        offering_finish_date = ""
                        for tarih in tarihler:
                            date_count = date_count + 1
                            tam_tarih = f"{tarih} {ay} {yil}"
                            if not len(tarihler) == date_count and date_count == 1:
                                offering_start_date = tam_tarih
                            elif len(tarihler) == date_count:
                                offering_finish_date = tarih
                        cursor.execute('''
                                INSERT INTO halka_arz (company_name, stock_code, offering_date, web_url, participation_index,offering_start_date,offering_finish_date)
                                VALUES (?, ?, ?, ?, ?,?,?)
                            ''', (
                            company_name, stock_code, offering_date, web_url, participation_index, offering_start_date, offering_finish_date))
                        conn.commit()
                        # Yeni veriyi mesaj olarak gönder
                        message = f"Yeni Halka Arz Tespit Edildi:\n\nFirma:\n{company_name}\n\nHalka Arz Tarihi:\n{offering_date}\n\nFirma Sitesi:\n{web_url}\n\nKatılım Endeksi:\n{participation_index}"
                        bot.send_message(CHAT_ID, message)
                        count_arz = count_arz + 1
                    server.quit()
        if count_arz == 0:
            anlik_tarih_ve_saat = datetime.datetime.now()
            hedef_tarih = anlik_tarih_ve_saat.strftime("%d %B %Y")

            conn_count = sqlite3.connect('halka_arz.db')
            cursor_count = conn_count.cursor()

            # SQL sorgusu
            sorgu = """
               SELECT *
               FROM halka_arz
               WHERE offering_start_date <= ? AND offering_finish_date >= ?
               """

            # Sorguyu çalıştır
            cursor_count.execute(sorgu, (hedef_tarih, hedef_tarih))

            # Sonuçları al
            sonuclar = cursor_count.fetchall()
            sonuclar_count = len(sonuclar)
            if sonuclar_count == 0:
                bot.send_message(CHAT_ID,
                                 f"Şuanda sistemde kayıtlı olmayan yeni bir halka arz bulunamadı. Sistemde bu gün için 0 halka arz mevcut daha sonra tekrardan \n- /arzsearch\n komutunu kullanabilir ve halka arzları yakalayabilirsiniz")
            else:
                bot.send_message(CHAT_ID,
                                 f"Şuanda sistemde kayıtlı olmayan yeni bir halka arz bulunamadı. Sistemde bu gün için {sonuclar_count} halka arz mevcut görmek için \n- /arznow\n komutunu kullanabilirsiniz")
        print(f"HTTP İsteği Başarılı! {datetime.datetime.now()}")
    else:
        print(f"HTTP İsteği Başarısız! Kod: {response_status_code}")
        bot.send_message(CHAT_ID,
                         f"Halka arz sistemi tarafından engellendim.\n Şuanda farklı IP adreslerinden sunucuya erişmeye çalışıyorum lütfen daha sonra tekrar deneyiniz.")
    conn.close()
    driver.quit()


# /start komutuna yanıt verme


@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = """Merhaba! Ben bir Halka Arz Botuyum 🤖

Beni kullanarak halka arzlar hakkında bilgi edinebilirsiniz. Aşağıdaki komutları kullanarak nasıl yardımcı olabileceğimi öğrenebilirsiniz:

- /arzsearch - Bazı arzlar sistemimde kayıtlı olmayabilir bunları internet ortamında tarayarak sistemime eklerim.
- /arznow - Sistemimde kayıtlı olan bu gün içerisinde bir halka arz varsa bunu size getiririm.

Bana aşağıdaki komutları kullanarak erişebilirsiniz:

- /start - Bu mesajı tekrar görüntüler.
- /help - Nasıl kullanılacağınızı daha fazla öğrenin.


Halka arzlar hakkında size yardımcı olmaktan mutluluk duyarım. Başlamak için lütfen /arzsearch komutunu kullanın ve daha sonra /arznow komutu ile bu gün bir halka arz var mı öğrenebilirsiniz. 🚀"""
    bot.reply_to(message, text)


# /help komutuna yanıt verme
@bot.message_handler(commands=['help'])
def send_help(message):
    mesaj = "Yardım Servisi "
    bot.send_message(message.chat.id, mesaj, parse_mode="Markdown")


@bot.message_handler(commands=['arzsearch'])
def send_arz(message):
    mesaj = "Talebiniz Alındı Halka Arzlar Taranıyor."
    bot.send_message(message.chat.id, mesaj, parse_mode="Markdown")
    send_periodic_message()


@bot.message_handler(commands=['arznow'])
def send_arz_now(message):
    print(message)
    # Veritabanına bağlan
    conn = sqlite3.connect('halka_arz.db')
    cursor = conn.cursor()

    anlik_tarih_ve_saat = datetime.datetime.now()
    hedef_tarih = anlik_tarih_ve_saat.strftime("%d %B %Y")

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
        id, stock_code, company_name, offering_date, web_url, participation_index, offering_start_date, offering_finish_date = sonuc
        message = f"Yeni Halka Arz Tespit Edildi:\n\nFirma: {company_name}\n\nHalka Arz Tarihi: {offering_date}\n\nFirma Sitesi: {web_url}\n\nKatılım Endeksi: {participation_index}"
        bot.send_message(CHAT_ID, message)

    if not sonuclar:
        message = f"Bu gün geçerli olan bir halka arz bulunamadı"
        bot.send_message(CHAT_ID, message)
    # Bağlantıyı kapat

    conn.close()


# Botu çalıştırın ve mesaj gönderme işlemini başlatın
if __name__ == "__main__":
    bot.polling()
