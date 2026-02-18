# Polymarket Bot Yol Haritası (Faz 0–8)

Bu doküman, Polymarket üzerinde otomatik işlem botu geliştirme sürecini fazlara ayrılmış şekilde tanımlar.

## Faz 0 — Kapsam ve Kararlar (Policy Lock)

### Trading Policy
- **Hedef pazar sınıfı:** Öncelik kripto, sonra yüksek hacimli spor marketleri, en son whitelist ile diğer marketler.
- **Seçim kriterleri:** 24s hacim, spread, top-of-book derinliği, resolution uzaklığı, outcome kalitesi.
- **İşlem ufku:** Kısa/orta vadeli, maker ağırlıklı yaklaşım.
- **Sermaye ve limitler:**
  - Market başına max notional
  - Event başına net/gross inventory limiti
  - Günlük/haftalık max drawdown
- **Market filtreleri:** negRisk/augmented negRisk marketlerinde `Other/placeholder` outcome dışlanır.
- **Fee-enabled market yaklaşımı:** feeRateBps runtime fetch; edge-after-fees <= 0 ise işlem yok.

### Ops Policy
- **Deploy region:** Geoblock uyumu > latency > kararlılık.
- **Anahtar saklama:** Prod’da KMS/HSM; düz metin private key yasak.
- **İmza modeli:** proxy wallet varsayılan; signer/funder ayrımı startup’ta doğrulanır.
- **Gözlemleme:** reject rate, confirm latency, WSS health, reconciliation lag alarmı.
- **Kill-switch:** geoblock flip, drawdown breach, reject storm, WSS sağlık bozulması.

### Varsayımlar
- Varsayım: feeRateBps ve tick size güncel olarak API’lerden çekilebilir.
- Varsayım: User WSS order lifecycle durumlarını güvenilir taşır.

### Riskler ve mitigasyonlar
- Tick/fee değişiminden emir reddi → pre-trade validator + kısa TTL cache.
- Düşük likiditede inventory kilitlenmesi → inventory cap + de-risk modu.
- Geoblock belirsizliği → default read-only fail-safe.

### Kabul kriterleri
- Policy dokümanı onaylı ve versiyonlu.
- Limitler config’te sayısal eşiklerle tanımlı.
- `Other/placeholder` dışlama testleri %100 geçer.

### Minimum test senaryoları
1. Fee-enabled markette feeRateBps eksikliği.
2. Tick size değişiminde eski fiyatla emir üretim denemesi.
3. `Other` outcome filtre testleri.
4. Drawdown breach sonrası trading halt.

---

## Faz 1 — Mimari + Read-only İskelet

### Bileşenler
- Ingest: market WSS + user WSS + REST snapshot.
- State store: Redis (hot state), Postgres (kalıcı event).
- Monitoring: metrics/logs/traces.

### Veri akışı
1. Gamma metadata alınır.
2. Market WSS book/price_change/last_trade eventleri işlenir.
3. User WSS lifecycle eventleri kalıcı yazılır.
4. REST snapshot ile periyodik doğrulama yapılır.
5. Reconciler gap/sapma durumunda snapshot bazlı düzeltme yapar.

### Reconciliation algoritması
- WSS incremental uygula → seq/gap kontrol et → gap varsa REST snapshot al → state’i atomik yenile → buffer’daki eventleri tekrar uygula → checksum doğrula.

### Rate limit ve dayanıklılık
- Global limiter + endpoint bazlı bütçe.
- Exponential backoff + jitter.
- Circuit breaker (open/half-open/close).
- WSS ping/pong + reconnect stratejisi.

### Varsayımlar
- Varsayım: Snapshot endpoint’leri kullanılabilir durumda.

### Riskler ve mitigasyonlar
- Mesaj kaybı → gap detection + snapshot recovery.
- 429/5xx artışı → adaptive throttling.

### Kabul kriterleri
- 24 saat read-only koşuda reconcile başarı oranı > %99.
- WSS kesintisinden toparlanma p95 < 60 sn.

### Minimum test senaryoları
1. WSS paket kaybı.
2. REST 429/5xx.
3. Seq gap.
4. Reconnect fırtınası.

---

## Faz 2 — Uyum + Güvenlik Zorunluları

### Geoblock Guard
- Startup geoblock check + periyodik tekrar.
- Engelli durumda read-only + alarm (+ policy’ye bağlı cancel-all).
- Endpoint erişilemiyorsa default deny trading.

### Identity & Wallet
- signer/funder/sig type zorunlu doğrulama.
- EOA vs proxy wallet için farklı config şeması.

### Supply-chain planı
- Official client dışı paket yasağı (istisna süreçli).
- Allowlist + lockfile pin + SCA + SBOM + checksum.

### Secret yönetimi
- Dev/staging/prod ayrımı.
- Rotasyon + audit log + least privilege.

### Varsayımlar
- Varsayım: CI’da SCA/SBOM adımları çalıştırılabilir.

### Riskler ve mitigasyonlar
- Typosquat → allowlist ve kilitli bağımlılık.
- Key sızıntısı → KMS/Vault ve erişim denetimi.

### Kabul kriterleri
- Geoblock fail durumunda bot read-only moda geçer.
- signer/funder mismatch’te servis start etmez.
- Her release’te SBOM/SCA raporu üretilir.

### Minimum test senaryoları
1. Geoblock timeout.
2. signature_type mismatch.
3. Yetkisiz secret erişimi.
4. Allowlist dışı paket denemesi.

---

## Faz 3 — Execution Engine

### Modüller
- Order validator: tick/min size/expiration/nonce.
- Fee service: feeRateBps fetch + kısa TTL cache + invalidation.
- Order router: post/cancel/replace.
- Idempotency store: duplicate engelleme.
- Signature adapter: official client interface soyutlaması.

### Lifecycle state machine
`NEW -> POSTED -> MATCHED -> MINED -> CONFIRMED`

Hata yolları: `RETRYING`, `FAILED`, `CANCELED`.

- MATCHED ama CONFIRMED değilse risk rezervi tutulur.
- Timeout ve retry/backoff kuralları idempotent çalışır.

### Trade muhasebe
- Parçalı fill birleştirme: order_id + bucket_index + match_time.
- Realized/unrealized PnL kaynakları standartlaştırılır.

### Operasyonel metrikler
- Reject reason dağılımı
- Post success rate
- Confirm latency
- Cancel ratio

### Varsayımlar
- Varsayım: User WSS lifecycle eventleri yeterli detay taşır.

### Riskler ve mitigasyonlar
- Hatalı fee cache → kısa TTL + reject sonrası refetch.
- WSS kopması → REST reconciliation + risk lock.

### Kabul kriterleri
- Fee-enabled markette feeRateBps olmadan order üretimi %0.
- Tick kaynaklı reject oranı staging’de hedef altı.

### Minimum test senaryoları
1. tick_size_change sırasında replace.
2. feeRateBps eksik/yanlış.
3. WSS koparken lifecycle takibi.
4. Tekrar post denemelerinde idempotency.

---

## Faz 4 — Risk Motoru + Kill-switch

### Prensipler
- Risk motoru stratejiye veto koyabilir.
- Belirsizlikte küçül veya dur.

### Limit sistemi
- Max notional (global/market/event)
- Max net/gross inventory
- Max open orders
- Max cancel/reject rate

### Drawdown & equity
- Peak equity takibi
- Günlük reset
- Realized/unrealized ayrımı

### Kill-switch tetikleri
- Geoblock flip
- WSS health bozulması
- Reconciliation failure
- Reject storm

### Decision pipeline
Strateji sinyali → risk filtresi → clamp/scale → order proposal.

### Varsayımlar
- Varsayım: Equity hesaplaması için güvenilir fiyat kaynağı var.

### Riskler ve mitigasyonlar
- Unrealized hesap hatası → tek marking standardı.
- Reject storm’da churn → hızlı halt + cooldown.

### Kabul kriterleri
- Limit aşan order proposal %0.
- DD breach sonrası belirlenen sürede trading halt.

### Minimum test senaryoları
1. DD breach.
2. Reconcile fail zinciri.
3. Reject storm.
4. Geoblock flip.

---

## Faz 5 — Backtest & Simülasyon

### Veri toplama
- prices-history, snapshot, incremental WSS, trade, metadata.
- Format: Parquet; partition: tarih/market/stream.
- Snapshot + incremental + checksum akışı.

### Seviye 1 (hızlı)
- Fiyat tabanlı kaba eleme.
- Fee/slippage kaba modeli.

### Seviye 2 (LOB sim)
- Queue/partial fill/cancel/adverse selection varsayımları.
- tick_size_change ve feeRateBps rejimi dahil.

### Overfitting önleme
- OOS split.
- Deney kayıt disiplini.
- Selection bias kontrolleri.

### Varsayımlar
- Varsayım: Replay deterministik seed ile çalıştırılabilir.

### Riskler ve mitigasyonlar
- Fazla iyimser fill modeli → konservatif worst-case senaryolar.

### Kabul kriterleri
- Aynı seed ile birebir tekrar edilebilir sonuç.
- IS/OOS metrikleri ayrı raporlanır.

### Minimum test senaryoları
1. Replay determinism.
2. Tick change günü replay.
3. Fee rejimi değişim testi.
4. Parçalı fill muhasebe invariants.

---

## Faz 6 — Strateji MVP Paketleri

### Plugin interface
- Input: feature set.
- Output: proposed orders + risk hints.

### MVP #1 — Maker MM
- Quote logic + refresh + inventory skew + postOnly.
- Rebate-aware spread ayarı.
- **Çalışır:** düşük/orta volatilite, yeterli derinlik.
- **Kapanır:** hızlı trend, spread patlaması.

### MVP #2 — Kontrollü momentum (taker)
- Sinyal + giriş/çıkış + edge-after-fees filtresi.
- Whipsaw filtresi.
- **Çalışır:** yönlü akış.
- **Kapanır:** chop + yüksek işlem maliyeti.

### MVP #3 — Cross-market (whitelist)
- Sadece güvenli whitelist ilişkileri.
- negRisk augmented `Other/placeholder` kesin dışarıda.
- **Çalışır:** ilişki stabil.
- **Kapanır:** korelasyon kırılması / veri asenkronisi.

### Varsayımlar
- Varsayım: Execution katmanı tick/fee doğruluğunu garanti eder.

### Riskler ve mitigasyonlar
- MM adverse selection → spread adaptasyonu.
- Momentum fee erozyonu → edge gate.

### Kabul kriterleri
- Paper trading hedef metrikleri strateji bazında tanımlı.

### Minimum test senaryoları
1. Risk veto testleri.
2. Volatilite şoku.
3. Whipsaw dönemi.
4. Veri gecikmesi/asenkroni.

---

## Faz 7 — Paper → Live Geçiş

### Rollout aşamaları
1. Read-only prod
2. Paper
3. Micro-live A
4. Micro-live B
5. Controlled live

Her aşamada somut limitler: market sayısı, max notional, max inventory, max günlük DD.

### Go/No-Go checklist
- Reconcile başarı
- WSS uptime
- Reject rate
- Confirm latency
- DD/kill-switch sağlığı

### Operasyon prosedürleri
- Deploy canary + rollback
- Config change onay akışı
- Emergency stop + cancel-all adımları

### Runbook
- WSS down
- Geoblock flip
- feeRateBps/tick sorunları
- Büyük fiyat şoku

### Varsayımlar
- Varsayım: Paper ve live aynı kod yolunu paylaşır.

### Riskler ve mitigasyonlar
- Aşama atlama baskısı → metrik temelli kapılar.

### Kabul kriterleri
- Her aşama minimum stabil koşu süresiyle tamamlanır.

### Minimum test senaryoları
1. Stage yükseltme/rollback dry-run.
2. Emergency stop tatbikatı.
3. Olay anı runbook uygulaması.

---

## Faz 8 — Sertleştirme & Ölçek

### Ölçekleme
- conditionId/tokenId tabanlı sharding.
- shard başına bağımsız ingest/state worker.
- backpressure kontrollü kuyruklama.

### Dayanıklılık
- Failover planı.
- Reconciliation hardening.
- Replay’e uygun stream/queue yaklaşımı.

### Güvenlik olgunluğu
- İmza servisleştirme.
- Rotasyon otomasyonu.
- Audit ve erişim kontrolü.

### Data & incident
- Ham event + snapshot + config versiyonlu replay pipeline.
- Olay sonrası analiz şablonu.

### Varsayımlar
- Varsayım: Sürekli arşivleme altyapısı kurulabilir.

### Riskler ve mitigasyonlar
- Shard dengesizliği → dinamik rebalancing.
- Uzun koşuda kaynak sızıntısı → soak test + sağlık yeniden başlatma politikası.

### Kabul kriterleri
- Haftalar ölçeğinde uptime/reconcile/MTTR hedefleri sağlanır.

### Minimum test senaryoları
1. Multi-shard soak test.
2. Failover tatbikatı.
3. Backpressure yük testi.
4. Incident replay doğrulaması.
