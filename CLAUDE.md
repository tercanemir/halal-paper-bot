# CLAUDE.md — Halal Paper Bot

> Read end-to-end before editing. Single source of truth for what this project is and isn't.

## 0. About Emir

- 18 yaşında (2026-05-17 itibarıyla). Yatırım konusunda yeni, finansal/yasal konularda tedbirli.
- Türkçe konuş, kod İngilizce.
- Direkt cevap, gereksiz disclaimer yok.
- **Hard constraint:** Hiçbir banka veya brokerage hesabı açamaz / açmak istemez. Bu yüzden bu proje gerçek paraya hiç dokunmuyor.
- Canonical user profile: `C:\Users\useer\.claude\projects\c--Users-useer-web-site\memory\user_emir.md`

## 1. Bu Proje Nedir

Yahoo Finance'tan ücretsiz hisse verisi çeken, katılım uyumlu US hisselerinden momentum stratejisi çalıştıran, **simüle edilmiş** trade'leri CSV/JSON dosyalarına yazan bir Python scripti. Gerçek hiçbir şey yok: hesap yok, broker yok, para hareketi yok.

Amaç: 3-6 ay çalıştırıp gerçek piyasa verisiyle stratejinin paper performansını ölçmek. İleride hayat şartları değişirse `paper_book.py`'yi broker SDK'sıyla değiştirip gerçeğe çevirme seçeneği açık.

## 2. Bu Proje Ne Değildir

- Gerçek trading sistemi değil
- Broker'a bağlanmıyor
- Optimizasyon vaadi yok (basit momentum stratejisi, eğitim amaçlı)
- Diğer projelerle (ROBUI, ai-trader-bot) hiçbir bağı yok, ayrı klasör, ayrı repo

## 3. Tech Stack

- Python 3.10+
- yfinance (ücretsiz US hisse verisi)
- pandas
- python-dotenv
- Standard library: csv, json, logging, dataclasses

Eklemeden önce sor: pandas-ta? sklearn? matplotlib? — Şimdilik yasak, MVP'yi karmaşıklaştırmaz.

## 4. Dosya Haritası

| Dosya | Rol |
|---|---|
| `config.py` | Tüm ayarlar (.env'den okur) |
| `universe.py` | Halal hisse listesi yükleyici (`data/halal_us_stocks.csv`) |
| `market.py` | yfinance wrapper: `latest_close`, `history`, `momentum_scores` |
| `paper_book.py` | Sanal portföy: cash, positions.json, trades.csv, equity_history.csv |
| `strategy.py` | Saf karar fonksiyonu: state + prices → list[Order] |
| `tick.py` | Günlük runner: GitHub Actions cron'dan tetiklenir |
| `status.py` | Human-readable rapor |
| `.github/workflows/bot.yml` | Daily cron + commit-back state files |
| `data/halal_us_stocks.csv` | Manuel curated halal evren |
| `data/trades.csv` | Append-only işlem geçmişi |
| `data/positions.json` | Şu anki holdings |
| `data/equity_history.csv` | Günlük end-of-day snapshot |

## 5. Strateji Kuralları (mevcut MVP)

- **Universe:** `data/halal_us_stocks.csv` — 40 büyük US hissesi, Wahed HLAL'a yakın
- **Sinyal:** Aylık rebalance, top-5 hisse 6 aylık momentum'a göre, eşit ağırlık
- **Stop-loss:** Avg cost'un %15 altında otomatik sat
- **Cash management:** Sells önce çalışır, sonra buys; cash yetersizse buy quantity ölçeklenir
- **Rebalance günü:** Her ayın ilk iş günü (Pzt-Cum, ayın 1-7'si arası)

## 6. Sert Kurallar

### 6.1 Gerçek borsaya kesinlikle bağlanma
Bu proje paper-only. Hiçbir broker SDK'sı (ib_insync, alpaca, robinhood, vs.) eklenmez. Emir explicit "şimdi gerçeğe çevirelim" demeden bu kural kırılmaz.

### 6.2 State integrity
`data/trades.csv` append-only. Asla sil, asla rewrite. Geçmişi koru — 3 ay sonra audit edilebilmeli.

### 6.3 Pure strategy
`strategy.py` saf fonksiyon: state + prices girdi, orders çıktı. Side effect yok. Test edilebilir kalsın.

### 6.4 Yfinance kırılırsa fallback yok
Veri kaynağı yfinance, ücretsiz ve garantisiz. Down olursa run skip. Backup veri kaynağı eklemiyoruz (Alpha Vantage, IEX, vs.) onaysız.

## 7. Konvansiyonlar

- Python 3.10+ syntax (type hints, `int | None`)
- Stdlib öncelik; pip pakedi eklemek için tartışılır
- Hiç comment ekleme, sadece *why* non-obvious ise tek satır
- English: code, comments, commits, identifiers
- Conventional commits: `feat:`, `fix:`, `refactor:`, `chore:`

## 8. Scope Dışı (sormadan ekleme)

- Backtesting engine (henüz yok; ileride)
- Real broker integration
- Multi-strategy support
- Web dashboard
- Telegram/Discord alerts (kullanıcı isterse eklenir)
- ML / sentiment analysis / haber tarama
- Diğer asset class'ları (crypto, forex, options)

## 9. Definition of Done

Her değişiklikten sonra:
1. `python tick.py` lokalde hatasız çalışır
2. `python status.py` mantıklı çıktı verir
3. `data/trades.csv` ve `data/equity_history.csv` bozulmaz
4. GitHub Actions yeşil

## 10. Quick Reference

```
Platform:       Pure paper, no broker
Data source:    yfinance (Yahoo Finance, free)
Universe:       ~40 halal US stocks (Wahed HLAL benzeri)
Strategy:       Monthly momentum, top 5, equal weight, 15% stop-loss
Starting cash:  $10,000 (virtual)
Run schedule:   GitHub Actions, weekdays after US close
State files:    data/trades.csv, data/positions.json, data/equity_history.csv
```

Real money: **NEVER** without Emir explicit go-ahead AND broker integration written from scratch in a separate branch.

---

*Last updated: 2026-05-17 (initial commit; paper-only design after Emir confirmed no bank/brokerage account possible).*
