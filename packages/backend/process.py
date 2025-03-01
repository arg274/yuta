from io import BytesIO
from typing import Optional, get_args
from fastapi import HTTPException, UploadFile
import pandas as pd
import scipy.io as sio
import numpy as np
import uuid

from ml.inference import predict_batch
from model.geomorph_web import GeomorphRequest, GeomorphResponse
from model.geomorph_data import ChannelType, GeomorphData
from model.graph_data import GraphData


def assign_channel_types(df: pd.DataFrame) -> pd.DataFrame:
    result_df = df.copy()

    theta_cols = ["theta_chi", "theta_sa", "rfit_theta_tt", "rfit_theta_tak"]
    result_df["avg_theta"] = result_df[theta_cols].mean(axis=1)

    conditions = [
        (result_df["avg_theta"] <= 0.2),
        (result_df["avg_theta"] > 0.2) & (result_df["avg_theta"] < 0.4),
        (result_df["avg_theta"] >= 0.4),
    ]
    choices = ["colluvial", "transitional", "fluvial"]

    result_df["channel_type"] = np.select(conditions, choices, default=None)

    return result_df


def calculate_channel_distribution(df: pd.DataFrame) -> GraphData:
    interpretable_df = df[df["interpretable_user"]]

    channel_counts = interpretable_df["channel_type"].value_counts()

    total_interpretable = len(interpretable_df)
    dist = {}

    for channel_type in get_args(ChannelType):
        count = channel_counts.get(channel_type, 0)
        dist[channel_type] = (
            float(count / total_interpretable) if total_interpretable > 0 else 0.0
        )

    return GraphData(dist=dist)


async def process_file(file: UploadFile) -> Optional[GeomorphResponse]:
    def process_csv(body: bytes) -> pd.DataFrame:
        _df = pd.read_csv(BytesIO(body))
        _df.rename(
            {
                "rfit_theta_tt": "rfit_thetaTT",
                "rfit_theta_tak": "rfit_thetaTAK",
            },
            inplace=True,
        )
        return _df

    def process_mat(body: bytes) -> pd.DataFrame:
        mat = sio.loadmat(BytesIO(body))

        columns = [
            "seg_length",
            "ksn",
            "theta_chi",
            "theta_sa",
            "rfit_theta_tt",
            "error_tt",
            "rfit_theta_tak",
            "error_tak",
            "stream",
        ]

        all_data = np.vstack([stream[0] for stream in mat["theta_cell"]])

        _df = pd.DataFrame(all_data, columns=columns)

        _df["stream"] = _df["stream"].astype(int)
        cols = ["stream"] + [col for col in _df.columns if col != "stream"]
        _df = _df[cols]

        return _df

    contents = await file.read()
    file_format = file.filename.split(".")[-1].lower()

    if file_format == "csv":
        df = process_csv(contents)
    elif file_format == "mat":
        df = process_mat(contents)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please use CSV or MAT format.",
        )

    return process_dataframe(df)


async def process_request(
    geomorph_request: GeomorphRequest,
) -> Optional[GeomorphResponse]:
    df = geomorph_request.to_df()
    return process_dataframe(df)


def process_dataframe(df: pd.DataFrame) -> Optional[GeomorphResponse]:
    df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    if "stream" in df.columns:
        df["stream"] = df["stream"].astype(int)

    preds = predict_batch(df)

    result_df = df.copy()

    for col in preds.columns:
        result_df[col] = preds[col]

    if "interpretable_user" not in result_df.columns:
        result_df["interpretable_user"] = result_df["interpretable"].copy()

    result_df = assign_channel_types(result_df)

    graph_data = calculate_channel_distribution(result_df)

    geomorph_data_list = []
    for _, row in result_df.iterrows():
        data_dict = row.to_dict()

        field_names = GeomorphData.__annotations__.keys()

        filtered_dict = {k: v for k, v in data_dict.items() if k in field_names}

        try:
            geomorph_data = GeomorphData(**filtered_dict)
            geomorph_data_list.append(geomorph_data)
        except Exception as e:
            print(f"Error creating GeomorphData: {e}")

    response = GeomorphResponse(data=geomorph_data_list, graph_data=graph_data)

    return response
