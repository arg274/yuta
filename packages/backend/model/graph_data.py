from typing import Dict
from pydantic import BaseModel

from .geomorph_data import ChannelType


class GraphData(BaseModel):
    dist: Dict[ChannelType, float]
