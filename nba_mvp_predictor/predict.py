from datetime import datetime
import json

from nba_mvp_predictor import conf, logger
from nba_mvp_predictor import load, preprocess, train


def load_model_make_predictions(max_n=50):
    model = load.load_model()
    data = load.load_silver_data()
    data = data.fillna(0.0)
    current_season = (
        datetime.now().year + 1 if datetime.now().month > 9 else datetime.now().year
    )
    logger.debug(f"Current season : {current_season}")
    data = data[data.SEASON == current_season]
    with open("data/features.json") as json_file:
        features_dict = json.load(json_file)
    cat = features_dict["cat"]
    num = features_dict["num"]
    features = features_dict["model"]
    min_max_scaling = False
    data_processed_features_only, _ = preprocess.scale_per_value_of(
        data, cat, num, data["SEASON"], min_max_scaler=min_max_scaling
    )
    X = data_processed_features_only[features]
    predictions = model.predict(X)
    data.loc[:, "PRED"] = predictions
    data.loc[:, "PRED_RANK"] = data["PRED"].rank(ascending=False)
    data = data.sort_values(by="PRED", ascending=False).head(max_n)
    data = data[data["PRED"]>0.0]
    data.to_csv(
        conf.data.predictions.path,
        sep=conf.data.predictions.sep,
        encoding=conf.data.predictions.encoding,
        compression=conf.data.predictions.compression,
        index=True,
    )
    try:
        history = load.load_history()
        logger.debug(f"History found - {len(history)} entries")
    except FileNotFoundError as e:
        history = {}
        logger.warning(f"No history found")
    history_entry = data["PRED"].to_dict()
    today = datetime.now().date().strftime("%d-%m-%Y")
    history[today] = history_entry
    with open(conf.data.history.path, "w", encoding=conf.data.history.encoding) as outfile:
        json.dump(history, outfile, indent=conf.data.history.indent)


def make_predictions():
    try:
        #train.make_bronze_data()
        #train.make_silver_data()
        load_model_make_predictions()
    except Exception as e:
        logger.error(f"Predicting failed : {e}")
