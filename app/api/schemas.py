from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class RunConfig(BaseModel):
    dataset_version: str
    cv: Dict
    model: Dict
    preprocess: Dict
    optuna: Optional[Dict] = None
    metric: str = Field(pattern="^(auc|f1|rmse|mae)$")
    seed: int

class RunResult(BaseModel):
    score: float
    cv_scores: List[float] = []
    artifacts: Dict   # keys: oof, submission, model, metrics, plots[]
    env: Dict
