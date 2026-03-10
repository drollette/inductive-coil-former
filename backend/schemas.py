"""Pydantic request/response models for the Inductive Parametric Coil API."""

from pydantic import BaseModel, Field


class CoilRequest(BaseModel):
    """Request parameters for generating an inductive coil former."""

    target_freq_mhz: float = Field(
        default=3.65, ge=1.0, le=60.0,
        description="Goal frequency in MHz"
    )
    current_res_mhz: float = Field(
        default=7.15, ge=1.0, le=60.0,
        description="Native resonance frequency in MHz"
    )
    velocity_factor: float = Field(
        default=0.96, ge=0.5, le=1.0,
        description="Velocity of Propagation (VOP)"
    )
    char_impedance_z0: float = Field(
        default=450, ge=50.0, le=1000.0,
        description="Average impedance of vertical (ohms)"
    )
    former_id: float = Field(
        default=57.0, ge=10.0, le=200.0,
        description="Former inner diameter in mm"
    )
    wire_copper_dia: float = Field(
        default=1.5, ge=0.5, le=6.0,
        description="Copper core diameter in mm"
    )
    insulation_thick: float = Field(
        default=0.15, ge=0.0, le=1.0,
        description="Insulation thickness on ONE side in mm"
    )
    wire_pitch: float = Field(
        default=2.0, ge=0.5, le=10.0,
        description="Distance between center of turns in mm"
    )
    wall_thickness: float = Field(
        default=3.5, ge=1.0, le=10.0,
        description="ASA wall thickness in mm"
    )
    clearance_fit: float = Field(
        default=0.5, ge=0.0, le=2.0,
        description="Slip-fit tolerance in mm"
    )
    groove_depth_ratio: float = Field(
        default=0.6, ge=0.1, le=0.9,
        description="How deep the wire sits (0.5 = half-buried)"
    )


class ComputedValues(BaseModel):
    """Computed geometry values returned by the API."""

    turns: int = Field(description="Number of coil turns")
    inductance_uh: float = Field(description="Required inductance in uH")
    wire_length_m: float = Field(description="Antenna wire length in m")
    coil_height: float = Field(description="Winding height in mm")
    total_height: float = Field(description="Total former height in mm")
    outer_diameter: float = Field(description="Former outer diameter in mm")
    total_wire_dia: float = Field(description="Total wire diameter (copper + insulation) in mm")


class CoilResponse(BaseModel):
    """Response containing generated file paths and computed values."""

    uuid: str = Field(description="Unique job identifier")
    computed: ComputedValues
    stl_url: str = Field(description="URL to download STL file")
    step_url: str = Field(description="URL to download STEP file")
