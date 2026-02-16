import pandas as pd
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
import joblib

load_dotenv(r"/home/ubuntu/tsx/data/data.env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE"),
    filemode='a'
)

base_file = os.getenv("FILE")
client_id = 1
filename = Path(f"{base_file}/{client_id}/file.csv")
df = pd.read_csv(filename)

try:
    df["cpu_next"] = df["cpu_percentage"].shift(-1)

    df = df.dropna(subset=["cpu_next"]).reset_index(drop=True)

    for lag in [1,2,3,4,5]:

        df[f'cpu_lag{lag}']   = df['cpu_percentage'].shift(lag)
        df[f'rps_lag{lag}']   = df['rps'].shift(lag)
        df[f'live_connection_lag{lag}']  = df['live_connections'].shift(lag)

    window = 5
    df['cpu_roll_mean'] = df['cpu_percentage'].rolling(window).mean()
    df['cpu_roll_std']  = df['cpu_percentage'].rolling(window).std()
    df['rps_roll_mean'] = df['rps'].rolling(window).mean()

    df = df.dropna().reset_index(drop=True)

    features = [col for col in df.columns if col.startswith(('cpu_', 'rps_', 'conn_', 'queue_pressure', 'live_connections', 'roll'))]

except Exception:

    logging.exception("Error caused during loading the model/files",
                      )

try:
    X = df[features]
    y = df["cpu_next"]

    total_rows = len(df)

    train_rows = int(total_rows*0.7)
    validate_rows = int(total_rows*0.15)
    test_rows  = total_rows - train_rows - validate_rows

    X_train = X.iloc[0 : train_rows]
    y_train = y.iloc[0 : train_rows]

    X_val = X.iloc[train_rows:train_rows+validate_rows]
    y_val = y.iloc[train_rows:train_rows+validate_rows]

    X_test = X.iloc[train_rows+validate_rows:]
    y_test = y.iloc[train_rows+validate_rows:]

except Exception:

    logging.exception("Error caused during spliting the data",
                      )

try:
    model = RandomForestRegressor(
        n_estimators=1000,
        max_depth= 7,
        min_samples_leaf=5,
        min_samples_split=10,
        random_state=42
    )

    model.fit(X_train, y_train)


except Exception:

    logging.exception("Error caused during the training the data")


joblib.dump(model,"model.pkl")
