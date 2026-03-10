"""
FastAPI application for the Inductive Parametric Coil Former generator.
Serves both the API and static frontend.
"""

import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import CoilRequest, CoilResponse, ComputedValues
from .geometry import build_coil_former, export_step, export_stl

BASE_DIR = Path(__file__).parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

OUTPUTS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Inductive Parametric Coil API",
    description="Parametric RF loading coil former generator with CadQuery",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def cleanup_job(job_id: str, delay: int = 3600) -> None:
    await asyncio.sleep(delay)
    job_dir = OUTPUTS_DIR / job_id
    shutil.rmtree(job_dir, ignore_errors=True)


@app.post("/generate", response_model=CoilResponse)
async def generate_coil(
    request: CoilRequest,
    background_tasks: BackgroundTasks,
) -> CoilResponse:
    job_id = str(uuid.uuid4())
    job_dir = OUTPUTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    result, info = build_coil_former(
        target_freq_mhz=request.target_freq_mhz,
        current_res_mhz=request.current_res_mhz,
        velocity_factor=request.velocity_factor,
        char_impedance_z0=request.char_impedance_z0,
        former_id=request.former_id,
        wire_copper_dia=request.wire_copper_dia,
        insulation_thick=request.insulation_thick,
        wire_pitch=request.wire_pitch,
        wall_thickness=request.wall_thickness,
        clearance_fit=request.clearance_fit,
        groove_depth_ratio=request.groove_depth_ratio,
    )

    stl_path = job_dir / "coil.stl"
    step_path = job_dir / "coil.step"

    export_stl(result, stl_path)
    export_step(result, step_path)

    background_tasks.add_task(cleanup_job, job_id)

    return CoilResponse(
        uuid=job_id,
        computed=ComputedValues(
            turns=info.turns,
            inductance_uh=round(info.inductance_uh, 2),
            wire_length_m=round(info.wire_length_m, 2),
            coil_height=round(info.coil_height, 2),
            total_height=round(info.total_height, 2),
            outer_diameter=round(info.outer_diameter, 2),
            total_wire_dia=round(info.total_wire_dia, 2),
        ),
        stl_url=f"/outputs/{job_id}/coil.stl",
        step_url=f"/outputs/{job_id}/coil.step",
    )


@app.get("/outputs/{job_id}/{filename}")
async def download_file(job_id: str, filename: str) -> FileResponse:
    file_path = OUTPUTS_DIR / job_id / filename

    if not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "application/octet-stream"
    if filename.endswith(".stl"):
        media_type = "model/stl"
    elif filename.endswith(".step"):
        media_type = "application/step"

    return FileResponse(path=file_path, media_type=media_type, filename=filename)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "version": "1.0.0"}


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
