# Automated Financial Ledger & Currency Converter

A modular, production-grade Python data pipeline that discovers raw multi-currency transaction records, standardizes text metadata, converts foreign exchange amounts in real time, and persists structured financial reports and visual analytics.


## Architecture Overview

The system processes financial records through a four-stage pipeline:

data/raw/**/*.csv  ──►  Recursive File Discovery & Stream Ingestion (os.walk, yield)
                                   │
                                   ▼
                        Text Cleaning & Tag Isolation (re)
                                   │
                                   ▼
                    Real-Time Currency Normalization (requests)
                                   │
                                   ▼
               Polymorphic Account Processing (ABC, Encapsulation)
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
data/reports/*.json       data/reports/*.csv        data/reports/*.png
 (Structured Summary)      (Flat Ledger Table)      (Visual Analytics)



1. **Ingestion & Parsing (`ledger/parser.py`):** Uses `os.walk` to find CSV files across nested fiscal folders and streams rows one at a time using Python generators (`yield`) to maintain an $O(1)$ memory footprint. RegEx isolates reference tags (e.g., `#INFRA-99`) from descriptions.
2. **Currency Conversion (`ledger/fx_service.py`):** Queries live exchange rates via a REST API to convert non-USD amounts to a standard base, with automatic fallback to static rates during network outages.
3. **Account Domain Logic (`ledger/accounts.py`):** Defines a strict `BaseAccount` abstract class. Concrete implementations (`SavingsAccount`, `CorporateAccount`) enforce domain invariants such as zero-overdraft rules and facility fee calculations.
4. **Export & Visual Analytics (`main.py`):** Calculates key aggregate metrics (inflows, outflows, net burn) using functional primitives (`sum`, `sorted`, `lambda`), then exports outputs to JSON, CSV, and a two-panel Matplotlib dashboard.



## Project Structure


financial_ledger/
├── data/
│   ├── raw/
│   │   ├── 2025/
│   │   │   └── q4_txns.csv       # Historical transaction input
│   │   └── 2026/
│   │       └── q1_txns.csv       # Current transaction input
│   └── reports/                  # Generated JSON, CSV, and PNG outputs
├── ledger/
│   ├── __init__.py
│   ├── accounts.py               # Abstract base classes and account entities
│   ├── fx_service.py             # Foreign exchange REST client & fallback logic
│   └── parser.py                 # File discovery, stream generator, RegEx parsing
├── tests/
│   └── __init__.py
├── main.py                       # Pipeline orchestration and reporting entrypoint
├── requirements.txt              # Project dependencies
└── README.md

```

---

## Prerequisites & Installation

* Python 3.10 or higher
* Git

### 1. Clone the Repository


git clone https://github.com/your-username/financial-ledger.git
cd financial-ledger

```

### 2. Set Up a Virtual Environment


# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

```

### 3. Install Dependencies


pip install -r requirements.txt

```

---

## Usage

Place raw `.csv` transaction files inside any subfolder under `data/raw/`, then execute the pipeline:


python main.py

```

### Expected Terminal Output


[*] Initializing Currency Converter...
[*] Bootstrapping account registries...
[*] Discovered 2 transaction files. Ingesting records...

Inflows:        $33,718.99 USD
Outflows:       $6,033.08 USD
Net cash flow:  $27,685.91 USD

Account balances:
  CORP-2001: $16,656.67 USD (statement fee: $25.00)
  SAV-1001:  $8,022.04 USD
  SAV-1002:  $3,007.20 USD

Top 3 expenses:
  TXN-25044   $2,630.34  Cloud infrastructure invoice
  TXN-26004   $1,875.00  Cloud hosting invoice
  TXN-26006     $848.00  Developer tools and licenses

[+] Output written to: data/reports/financial_summary.json
[+] Output written to: data/reports/processed_transactions.csv
[+] Output written to: data/reports/financial_dashboard.png

```

---

## Generated Artifacts

Executing the pipeline creates three files in `data/reports/`:

* **`financial_summary.json`**: Key performance indicators, account balances, and categorized records.
* **`processed_transactions.csv`**: Normalized ledger table ready for relational databases or spreadsheet tools.
* **`financial_dashboard.png`**: Matplotlib visualization showing:
* Account balance comparison bar chart.
* Cash inflow versus outflow distribution donut chart.



---

## Core Engineering Concepts Demonstrated

* **Object-Oriented Programming:** Abstract Base Classes (`abc.ABC`), protected attributes (`_balance`), private name-mangled tokens (`__auth_token`), and polymorphism.
* **Defensive Programming:** Multi-tiered exception handling (`KeyError`, `ZeroDivisionError`, `RequestException`) with automatic fallbacks for external APIs.
* **Memory Efficiency:** Python generator functions (`yield`) paired with `csv.DictReader` to stream tabular data without loading complete files into memory.
* **Pattern Matching:** Regular expressions (`re.search`, `re.sub`) to parse unstructured transaction tags.