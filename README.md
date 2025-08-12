## Plotly Dash MVVM Boilerplate

This repository contains a minimal yet solid boilerplate for building
interactive dashboards with [Dash](https://dash.plotly.com/) using
Plotly.  The project follows a structure inspired by the
Model‑View‑ViewModel (MVVM) pattern and adheres to the SOLID design
principles.  It is intended as a starting point for new projects and
demonstrates a clean separation of concerns between models,
view‑models, views and services.

### Features

- **Model layer** – Encapsulates the data structures and basic data
  loading logic.  The `DataModel` class is responsible for
  retrieving raw data and exposing it as a pandas `DataFrame`.
- **Service layer** – Provides an additional abstraction over
  external resources.  If your application communicates with
  databases, APIs or other services, it is best to wrap that logic
  here.  The included `DataService` simply delegates to the model
  but shows how services can be injected into higher layers.
- **ViewModel layer** – Orchestrates application logic and state.  It
  exposes methods and properties that the view can bind to.  The
  provided `DataViewModel` class computes derived values and is used
  by the Dash callbacks.
- **View layer** – Defines the user interface and callback functions.
  All Dash components live here.  The view delegates to its
  associated view‑model for data and exposes a `create_app` function
  that returns a fully configured `dash.Dash` instance.
- **SOLID principles** – Each class has a single responsibility,
  dependencies are injected where needed, and the architecture is
  open for extension but closed for modification.

### Installation

1. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python app.py
   ```

   The Dash server will start and can be accessed at
   `http://localhost:8050`.

### Structure

```
plotly_dash_mvvm/
├── app.py              # Entry point that wires together the layers
├── README.md           # Project documentation and usage instructions
├── requirements.txt    # Python dependencies
├── models/             # Data models describing the shape of the data
│   ├── __init__.py
│   └── data_model.py
├── services/           # Services encapsulating external resources
│   ├── __init__.py
│   └── data_service.py
├── viewmodels/         # ViewModels orchestrating UI state and logic
│   ├── __init__.py
│   └── data_viewmodel.py
├── views/              # Views that define Dash layout and callbacks
│   ├── __init__.py
│   └── dash_view.py
└── utils/              # Utility modules (configuration etc.)
    ├── __init__.py
    └── config.py
```

### Extending the boilerplate

- **Adding new pages** – Create a new view (e.g. `views/report_view.py`)
  along with its own view‑model.  Register the layout and callbacks
  in the main Dash application.
- **Connecting to a database or API** – Introduce new services that
  handle connections and interactions with external systems.  Inject
  those services into your view‑models.
- **Styling** – Dash allows you to define custom CSS or use the
  built‑in components from the `dash-bootstrap-components` library.
  To keep the example simple, default styles are used here.

Feel free to experiment and build upon this structure.  Happy
dashboarding!

## InfluxDB Integration

This project includes comprehensive InfluxDB integration for real-time data visualization. 
See **[INFLUXDB_GUIDE.md](INFLUXDB_GUIDE.md)** for detailed documentation covering:

- InfluxDB fundamentals and data model
- Flux query language examples
- Data discovery tools and techniques  
- Configuration and security best practices
- Troubleshooting common issues
- Developer extension guidelines

**Quick start:** Set connection variables in `.env` and use `scripts/discover_influx.py` to explore your data schema.

### Using InfluxDB as a Data Source

The boilerplate can pull live data from InfluxDB (v2) instead of the
synthetic sample dataset. This is enabled entirely through environment
variables—no code changes required.

Set the following variables (e.g. in a local `.env` or your shell
session). If any are missing the app falls back gracefully to the
synthetic data.

Required:

```
INFLUXDB_URL=https://influxdb.bantryprop.com
INFLUXDB_TOKEN=REDACTED_READ_TOKEN
INFLUXDB_ORG=systems-one
INFLUXDB_BUCKET=telemetry
INFLUXDB_MEASUREMENT=<measurement_name>
INFLUXDB_CATEGORY_TAG=<tag_used_for_category_grouping>
INFLUXDB_VALUE1_FIELD=<numeric_field_1>
INFLUXDB_VALUE2_FIELD=<numeric_field_2>
```

Optional:

```
INFLUXDB_RANGE_START=-1h   # Adjust time window, e.g. -24h, -7d
```

Example PowerShell (session only):

```powershell
$env:INFLUXDB_URL = "https://influxdb.bantryprop.com"
$env:INFLUXDB_TOKEN = "<READ_ONLY_TOKEN>"
$env:INFLUXDB_ORG = "systems-one"
$env:INFLUXDB_BUCKET = "telemetry"
$env:INFLUXDB_MEASUREMENT = "<measurement_name>"
$env:INFLUXDB_CATEGORY_TAG = "<tag_key>"
$env:INFLUXDB_VALUE1_FIELD = "<field1>"
$env:INFLUXDB_VALUE2_FIELD = "<field2>"
$env:INFLUXDB_RANGE_START = "-1h"
python app.py
```

Discovering names in the InfluxDB UI:

1. Measurement list: Data Explorer → select bucket `telemetry`, view
  Measurements panel.
2. Tag keys: In Script Editor run:
  ```flux
  import "influxdata/influxdb/schema"
  schema.tagKeys(bucket: "telemetry", start: -7d)
  ```
3. Field keys:
  ```flux
  import "influxdata/influxdb/schema"
  schema.fieldKeys(bucket: "telemetry", start: -7d)
  ```
4. Preview candidate fields:
  ```flux
  from(bucket: "telemetry")
    |> range(start: -15m)
    |> filter(fn: (r) => r._measurement == "<measurement_name>")
    |> limit(n: 10)
  ```

Security: never commit real tokens. Use environment variables or a
secrets manager. If a token leaks, revoke it in the InfluxDB UI and
generate a new read‑only token.