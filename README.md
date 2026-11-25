# Hotel Booking Cancellation Prediction

End-to-end data project on the public [Hotel Booking Demand](https://www.sciencedirect.com/science/article/pii/S2352340918315191) dataset (119,390 bookings, two Portuguese hotels, 2015-07 → 2017-08):
**PostgreSQL business analysis → EDA → leakage-aware ML model → containerised REST API.**

**Business question:** which bookings are likely to be canceled, so a hotel can act early (reminders, deposits, controlled overbooking) and protect revenue?

## Results at a glance

Time-based split (train < 2017-03, validation Mar–May 2017, **test Jun–Aug 2017**), exact duplicates removed. Decision threshold chosen on validation only.

| Model (test set) | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Majority baseline | 0.500 | 0.353 | – | – | – |
| Logistic regression | 0.820 | 0.693 | 0.566 | 0.827 | 0.672 |
| **LightGBM (shipped)** | **0.845** | **0.712** | 0.592 | 0.843 | **0.696** |
| LightGBM, booking-time features only* | 0.792 | 0.629 | 0.533 | 0.918 | 0.674 |

\*Drops `booking_changes`, `required_car_parking_spaces`, `total_of_special_requests`, which are often updated *after* booking (see [Limitations](#limitations)).

Key findings (from `sql/` and `reports/figures/`):

- **~27.5%** of de-duplicated bookings are canceled; City Hotel 30.1% vs Resort 23.5%.
- Cancellation climbs steadily with lead time: **8% (0–7 days) → 41% (>1 year)**.
- Estimated revenue lost to cancellations (ADR × nights) was **~€5.5M in 2017 (Jan–Aug)**, ~39% / 37% of booked revenue for City / Resort.
- Online travel agents are the riskiest channel (35.5% canceled, 60% of all bookings).
- Strong protective signals: special requests (21.7% vs 33.3%), repeat guests (7.7% vs 28.3%), changed bookings (15.5% vs 30.2%). Strong risk signal: a previous cancellation (68%).
- Most important raw features (permutation importance): country, agent, parking, special requests, lead time, market segment.

## Project structure

```
├── data/hotel_bookings.csv      # raw dataset
├── sql/                         # PostgreSQL: setup (materialized view + indexes) + 7 analytical queries
├── src/
│   ├── config.py                # paths, split dates
│   ├── features.py              # leakage-free feature engineering (lives inside the pipeline)
│   ├── pipeline.py              # sklearn pipelines (LogReg, LightGBM)
│   ├── train.py                 # time split, baselines, threshold, ablation, artifacts
│   ├── evaluate.py              # metrics & plots
│   ├── eda.py                   # EDA figures
│   ├── db.py                    # PostgreSQL connection, CSV bulk load (COPY), query helpers
│   ├── run_sql.py               # loads CSV into PostgreSQL, runs sql/*.sql
│   └── app.py                   # FastAPI service
├── tests/                       # pytest: features, API, SQL (integration)
├── models/model.joblib          # trained pipeline + threshold
├── reports/                     # metrics.json, figures/, sql_results/
├── docker-compose.yml · .env.example   # PostgreSQL (+ API) services
├── Dockerfile · Makefile · requirements*.txt · .github/workflows/ci.yml
```

## Methodology

1. **Cleaning** – removed 31,994 exact duplicate rows, 180 zero-guest rows and 1 negative-ADR row → 87,229 bookings.
2. **Leakage control** – excluded `reservation_status`, `reservation_status_date` (they *are* the outcome), `assigned_room_type` and `days_in_waiting_list`.
3. **Feature engineering** (inside the sklearn pipeline, so the API cannot diverge from training): arrival month/week/weekday, total nights, party size, weekend share, ADR per person, total price, prior-cancellation ratio, agent/company flags. `arrival_date_year` is deliberately not used.
4. **Validation** – chronological split instead of random: cancellation rate drifts from 25% (train) to 35% (test), which a random split would hide.
5. **Model** – LightGBM with small, strongly regularised trees (`num_leaves=7`), tuned on the validation set and early-stopped; compared against logistic regression and a majority baseline.
6. **Threshold** – maximises F1 on validation (0.21); the precision/recall trade-off plot is in `reports/figures/`. A hotel could instead pick the threshold from its own cost of an empty room vs. a walked guest.

## Quick start

```bash
pip install -r requirements-dev.txt

make db-up    # start PostgreSQL in Docker (docker compose up -d db)
make sql      # load CSV into Postgres + run the 7 queries -> reports/sql_results/
make eda      # EDA figures             -> reports/figures/
make train    # train + evaluate + save -> models/model.joblib, reports/metrics.json
make test     # pytest (SQL tests are skipped if Postgres is not running)
make serve    # API at http://localhost:8000/docs
make db-down  # stop PostgreSQL
```

### PostgreSQL

The database runs from `docker-compose.yml` (user/password/db: `hotel`, port 5432). Connection settings come from the `DATABASE_URL` environment variable and default to the compose database; copy `.env.example` to `.env` to use your own server.

```bash
# inspect the data yourself
docker exec -it hotel-postgres psql -U hotel -d hotel
hotel=# SELECT hotel, ROUND(100*AVG(is_canceled),1) AS cancel_pct FROM bookings GROUP BY hotel;
```

`sql/00_setup.sql` builds the `bookings` **materialized view** (de-duplicated, validated, enriched with dates and revenue) plus indexes; every analysis query reads from it.

### Docker

```bash
docker build -t hotel-cancellation-api .
docker run --rm -p 8000:8000 hotel-cancellation-api
```

### API example

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{
  "hotel": "City Hotel", "lead_time": 200, "arrival_date_year": 2017,
  "arrival_date_month": "August", "arrival_date_day_of_month": 10,
  "stays_in_weekend_nights": 2, "stays_in_week_nights": 3, "adults": 2,
  "market_segment": "Online TA", "adr": 120, "total_of_special_requests": 0
}'
# {"cancel_probability":0.7715,"will_cancel":true,"threshold_used":0.2098}
```

Endpoints: `GET /health`, `POST /predict` (interactive docs at `/docs`).

## Limitations

- **Post-booking features.** `required_car_parking_spaces` is 0% canceled in the data, so it is probably recorded during the stay. Together with `booking_changes` and special requests it inflates performance (AUC 0.845 vs 0.792 without them). For production scoring at booking time, use the booking-time-only variant.
- **Duplicates.** Dropping exact duplicates is a judgement call: some may be genuine identical group bookings. It removes most of the `Non Refund` rows (14.6k → 1k), which in the raw data are ~99% canceled, a known quirk of this dataset.
- **Two hotels, one country, 2 years.** Results may not transfer to other markets. Cancellation-rate drift suggests periodic retraining.
- The shipped model is trained on train-only data (test kept untouched); a production version would refit on all data.

## Possible next steps

Cost-based threshold, probability calibration, SHAP explanations, drift monitoring, CI/CD image publishing.

## License

See [LICENSE](LICENSE).
