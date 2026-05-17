# Halal Paper Bot

Tamamen simülasyon. Hiçbir borsaya bağlanmıyor, hiçbir gerçek emir vermiyor. Yahoo Finance'tan ücretsiz fiyat verisi çekiyor, katılım uyumlu US hisselerinden momentum stratejisiyle sanal portföy yönetiyor, her hareketi log'a yazıyor.

3 ay sonra `data/trades.csv` ve `data/equity_history.csv` dosyalarına bakarsın, hangi hisseyi ne zaman alıp sattığını ve toplam paper PnL'ini görürsün.

## Mantık

- **Evren:** `data/halal_us_stocks.csv` (40 hisse, manuel curated, Wahed HLAL'a yakın liste)
- **Strateji:** Her ayın ilk iş günü, evreni son 6 ay getirisine göre sırala, top 5 hisseyi eşit ağırlıkta tut
- **Stop-loss:** Pozisyonun ortalama maliyetinin %15 altına düşerse otomatik sat
- **Başlangıç sermayesi:** Sanal $10.000

## Çalıştırma

```
pip install -r requirements.txt
python tick.py     # bir günlük döngü: fiyat çek, karar ver, sanal emir, equity snapshot
python status.py   # mevcut sanal portföy + son işlemler
python universe.py # hisse listesini gör
```

`tick.py` GitHub Actions cron ile her iş günü tetiklenir.

## Dosyalar

| Dosya | Rol |
|---|---|
| `config.py` | Tüm ayarlar (sermaye, top N, lookback, stop loss) |
| `universe.py` | Halal hisse listesi yükleyici |
| `market.py` | yfinance wrapper (fiyat + momentum) |
| `paper_book.py` | Sanal portföy: cash, pozisyon, trade log, equity |
| `strategy.py` | Saf karar fonksiyonu: state in → orders out |
| `tick.py` | Günlük runner |
| `status.py` | İnsan okuyan rapor |
| `data/halal_us_stocks.csv` | Hisse evreni |
| `data/trades.csv` | Tüm işlem geçmişi (büyür) |
| `data/positions.json` | Şu anki pozisyonlar |
| `data/equity_history.csv` | Günlük equity snapshot |

## İleride

Eğer bir gün gerçek brokere bağlanmak istersen, yapacağın tek şey `paper_book.py`'yi `broker_book.py` ile değiştirip aynı `buy()`/`sell()` API'sini broker SDK'sına yönlendirmek. `strategy.py` ve `tick.py` değişmez.
