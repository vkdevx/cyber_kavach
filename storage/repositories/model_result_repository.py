from typing import List, Optional
from sqlalchemy.orm import Session
from storage.models_orm import ModelResultORM


class ModelResultRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_result(
        self,
        result_id: str,
        flow_id: str,
        rf_class: str,
        rf_probability: float,
        if_anomaly_score: float,
        model_version: str,
        inference_ts: float
    ) -> ModelResultORM:
        result = ModelResultORM(
            result_id=result_id,
            flow_id=flow_id,
            rf_class=rf_class,
            rf_probability=rf_probability,
            if_anomaly_score=if_anomaly_score,
            model_version=model_version,
            inference_ts=inference_ts
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_results_by_flow(self, flow_id: str) -> List[ModelResultORM]:
        return (
            self.db.query(ModelResultORM)
            .filter(ModelResultORM.flow_id == flow_id)
            .all()
        )
