# L3 · Introduction to Prediction Markets — materials for students

Stats C161/C261, guest lecture by Yurii Nosov (UCLA Trustworthy AI Lab), Thursday Oct 8, 2026.

## What is in this package

| File | What it is |
|---|---|
| `L3_prediction_markets_slides.pdf` | The lecture slides. |
| `Polymarket_Data_User_Guide.pdf` | The lab's data guide (by June Qin): the market catalog, resolutions, hourly order books, and per-wallet trade history. **Start here for the project.** |
| `notebooks/lab_database_walkthrough.ipynb` | Block 2 demo: query the catalog and rebuild an order book. The `.html` next to it shows the same notebook already run. |
| `notebooks/insider_demo.ipynb` | Block 3 demo: Isolation Forest on real wallets. Self-contained, runs offline on the CSVs in `notebooks/data/`. |
| `notebooks/data/wallet_features.csv` | One row per wallet (55,952), six features, `confirmed` = publicly identified insider. Wallet ids are pseudonymous. |
| `notebooks/data/wallet_scores.csv` | The same wallets with the Isolation Forest score and rank from the demo, for those who want to skip the fitting step. |

## The database password

Everywhere the guide shows `<PASSWORD>`, substitute the password given in class and posted on Bruin Learn.
Do not put the password in any file you upload to GitHub or share outside the class.

## Setup (once)

```
pip install pandas duckdb sqlalchemy psycopg2-binary pyarrow python-dotenv matplotlib scikit-learn jupyter
```

For `lab_database_walkthrough.ipynb`, create a plain text file named `.env` in the `notebooks/` folder with this one line,
user, password and host filled in (from Bruin Learn):

```
JUNE_DB_URL=postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/postgres
```

`insider_demo.ipynb` needs no password and no network.

## On campus: use eduroam, not UCLA_WEB

UCLA_WEB blocks the database port, so the catalog queries hang. eduroam works. The order-book and wallet-trade files
(the public `cloudfront.net` URLs in the guide) work on any network.

## Questions

Ask on the course forum, or email yuriinosov@ucla.edu.
