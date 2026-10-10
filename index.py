
import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).with_name("telemetry.jsonl")


class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float = 180


@app.get("/")
def home():
    return {"message": "eShopCo API is running"}


@app.post("/")
def calculate_metrics(request: MetricsRequest):
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            records = json.load(f)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load telemetry data: {exc}",
        )

    result = {}

    for region in request.regions:
        rows = [
            r for r in records
            if r["region"].lower() == region.lower()
        ]

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No data for region: {region}",
            )

        latencies = np.array(
            [float(r["latency_ms"]) for r in rows]
        )
        uptimes = np.array(
            [float(r["uptime_pct"]) for r in rows]
        )

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int(
                np.sum(latencies > request.threshold_ms)
            ),
        }

    return result
