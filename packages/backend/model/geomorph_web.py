from typing import List
import pandas as pd
from pydantic import BaseModel

from .geomorph_data import GeomorphData
from .graph_data import GraphData


class GeomorphResponse(BaseModel):
    data: List[GeomorphData]
    graph_data: GraphData


class GeomorphRequest(BaseModel):
    data: List[GeomorphData]

    def to_df(self) -> pd.DataFrame:
        data_dicts = [data.model_dump() for data in self.data]

        df = pd.DataFrame(data_dicts)

        return df
