import pandas as pd
from .model_manager import ModelManager


def predict_batch(data: pd.DataFrame) -> pd.DataFrame:
    """Make predictions for multiple samples from a CSV file"""
    mm = ModelManager()
    model = mm.model
    le = mm.label_encoder

    column_mapping = {
        "rfit_theta_tt": "rfit_thetaTT",
        "rfit_theta_tak": "rfit_thetaTAK",
    }

    df_model = data.copy()

    df_model.rename(columns=column_mapping, inplace=True)

    features = ["theta_chi", "theta_sa", "rfit_thetaTT", "rfit_thetaTAK"]

    if not all(feat in df_model.columns for feat in features):
        missing = [feat for feat in features if feat not in df_model.columns]
        raise ValueError(f"Missing features in input data: {missing}")

    predictions = model.predict(df_model[features])
    probabilities = model.predict_proba(df_model[features])

    results = pd.DataFrame()
    results["prediction"] = le.inverse_transform(predictions)
    results["confidence"] = [max(p) for p in probabilities]

    results["interpretable"] = results["prediction"] == "I"
    results["interpret_confidence"] = results["confidence"]

    return results
