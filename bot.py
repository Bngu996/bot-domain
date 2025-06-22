import telebot
import requests
import threading
import time
import os

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
DOMAIN_FILE = 'domains.txt'

if not TOKEN or not CHAT_ID:
    print("ERROR: TOKEN atau CHAT_ID tidak ditemukan di environment variables.")
    exit()

bot = telebot.TeleBot(TOKEN)

def is_valid_domain(domain):
    if '.' in domain and ' ' not in domain and len(domain) > 3:
        return True
    return False

def is_admin(chat_id):
    return str(chat_id) == str(CHAT_ID)

@bot.message_handler(commands=['add'])
def add_domain(message):
    if not is_admin(message.chat.id):
        return
    try:
        domain_to_add = message.text.split(maxsplit=1)[1].strip().lower()
        if not is_valid_domain(domain_to_add):
            bot.reply_to(message, "Format domain tidak valid.")
            return
    except IndexError:
        bot.reply_to(message, "Penggunaan: /add contoh.com")
        return
    
    if not os.path.exists(DOMAIN_FILE):
        open(DOMAIN_FILE, 'w').close()
    
    with open(DOMAIN_FILE, 'r') as f:
        existing_domains = [line.strip().lower() for line in f]
    
    if domain_to_add in existing_domains:
        bot.reply_to(message, f"`{domain_to_add}` sudah ada.", parse_mode="Markdown")
        return
    
    with open(DOMAIN_FILE, 'a') as f:
        f.write(f"{domain_to_add}\n")
    bot.reply_to(message, f"`{domain_to_add}` berhasil ditambahkan.", parse_mode="Markdown")

@bot.message_handler(commands=['delete'])
def delete_domain(message):
    if not is_admin(message.chat.id):
        return
    try:
        domain_to_delete = message.text.split(maxsplit=1)[1].strip().lower()
    except IndexError:
        bot.reply_to(message, "Penggunaan: /delete contoh.com")
        return
    
    if not os.path.exists(DOMAIN_FILE):
        bot.reply_to(message, "File domain tidak ditemukan.")
        return

    with open(DOMAIN_FILE, 'r') as f:
        lines = f.readlines()
    
    new_lines = [line for line in lines if line.strip().lower() != domain_to_delete]
    
    if len(lines) == len(new_lines):
        bot.reply_to(message, f"`{domain_to_delete}` tidak ditemukan.", parse_mode="Markdown")
        return
    
    with open(DOMAIN_FILE, 'w') as f:
        f.writelines(new_lines)
    bot.reply_to(message, f"`{domain_to_delete}` berhasil dihapus.", parse_mode="Markdown")

def cek_domain():
    if not os.path.exists(DOMAIN_FILE) or os.path.getsize(DOMAIN_FILE) == 0:
        return "Belum ada domain untuk diperiksa. Gunakan `/add`."

    with open(DOMAIN_FILE, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    if not domains:
         return "Daftar domain kosong. Gunakan `/add`."
    
    status_report = "<b>Laporan Status Domain</b>\n\n"
    for domain in domains:
        try:
            response = requests.get(f'https://isthisblocked.com/api/check?host={domain}')
            if response.status_code == 200:
                data = response.json()
                if data.get('blocked'):
                    status_report += f"{domain}: 🔴 Diblokir\n"
                else:
                    status_report += f"{domain}: 🟢 Tidak Diblokir\n"
            else:
                status_report += f"{domain}: ⚠️ Error (HTTP {response.status_code})\n"
        except Exception as e:
            status_report += f"{domain}: ⚠️ Gagal memeriksa\n"
    return status_report

def kirim_pesan_loop():
    print("Memulai loop pengecekan domain...")
    while True:
        try:
            pesan = cek_domain()
            bot.send_message(CHAT_ID, pesan, parse_mode='HTML', disable_web_page_preview=True)
            print(f"Laporan terkirim ke {CHAT_ID}")
        except Exception as e:
            print(f"Gagal mengirim pesan: {e}")
        time.sleep(1800)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_admin(message.chat.id):
        return
    bot.reply_to(message, "Bot aktif. Laporan akan dikirim setiap 30 menit.")
    # Langsung kirim laporan pertama saat /start
    try:
        pesan = cek_domain()
        bot.send_message(CHAT_ID, pesan, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print(f"Gagal mengirim laporan awal: {e}")


print("Bot memulai...")
threading.Thread(target=kirim_pesan_loop, daemon=True).start()
print("Polling dimulai...")
bot.infinity_polling()
