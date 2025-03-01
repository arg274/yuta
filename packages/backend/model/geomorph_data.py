from typing import Literal, Optional, TypeAlias
from pydantic import BaseModel


ChannelType: TypeAlias = Literal["fluvial", "transitional", "colluvial"]


class GeomorphData(BaseModel):
    id: str
    stream: int
    ksn: float
    theta_chi: float
    theta_sa: float
    rfit_theta_tt: float
    error_tt: float
    rfit_theta_tak: float
    error_tak: float
    interpretable: bool
    interpret_confidence: float
    interpretable_user: Optional[bool]
    channel_type: Optional[ChannelType]
