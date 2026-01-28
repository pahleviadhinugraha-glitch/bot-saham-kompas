import yfinance as yf
import pandas as pd
import requests
import os

# --- PENGATURAN KUNCI (DIAMBIL DARI LANGKAH 2) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
MODAL_PER_SAHAM = 10_000_000 # Alokasi 10 Juta per saham

def get_kompas100():
    """Mengambil daftar saham Kompas100 terbaru"""
    try:
        url = "https://id.wikipedia.org/wiki/Indeks_Kompas100"
        tables = pd.read_html(url)
        for df in tables:
            if 'Kode' in df.columns:
                return [t + ".JK" for t in df['Kode'].dropna().unique().tolist() if len(t) == 4]
    except:
        # Cadangan jika Wikipedia gagal diakses
        return ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "ANTM.JK"]

def screen_stocks():
    tickers = get_kompas100()
    hit_list = []
    
    for t in tickers:
        try:
            # Ambil data harga saham
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if len(df) < 40: continue
            
            # Hitung Fibonacci (Struktur High/Low 2 bulan terakhir)
            high_40 = df['High'].iloc[-40:].max()
            low_40 = df['Low'].iloc[-40:].min()
            price = df['Close'].iloc[-1]
            
            # Zona Diskon (Fibo 0.50 - 0.618)
            fibo_50 = high_40 - (0.50 * (high_40 - low_40))
            fibo_61 = high_40 - (0.618 * (high_40 - low_40))
            
            # Syarat: Di zona diskon DAN harga memantul (lebih tinggi dari High kemarin)
            if fibo_61 <= price <= fibo_50 and price > df['High'].iloc[-2]:
                lot = int(MODAL_PER_SAHAM / (price * 100))
                upside = ((high_40 / price) - 1) * 100
                
                hit_list.append(
                    f"✅ *{t}* (Sinyal Kompas100)\n"
                    f"Harga: Rp {price:.0f}\n"
                    f"Beli: *{lot} Lot* (Alokasi 10jt)\n"
                    f"Target TP: Rp {high_40:.0f} (+{upside:.1f}%)\n"
                    f"Stop Loss: Rp {price * 0.95:.0f} (-5%)"
                )
        except: continue

    # Kirim ke Telegram jika ada saham yang cocok
    if hit_list:
        msg = "💰 *IHSG PRO ALERT (Kompas100)*\n\n" + "\n\n".join(hit_list)
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}&parse_mode=Markdown")

if __name__ == "__main__":
    screen_stocks()
