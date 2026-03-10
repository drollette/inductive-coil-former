"""
CadQuery geometry engine for the Inductive Parametric Coil Former.
Based on W7HAK RF coil calculations with Wheeler's formula.
"""

import cadquery as cq
import math
from dataclasses import dataclass
from pathlib import Path

C = 299792458  # speed of light


@dataclass
class CoilInfo:
    """Computed geometry values for a coil former."""
    turns: int
    inductance_uh: float
    wire_length_m: float
    coil_height: float
    total_height: float
    outer_diameter: float
    total_wire_dia: float


def calc_inductance(f_target, l_wire, z0, vf):
    """Calculate required loading inductance in uH."""
    lam_target = (C * vf) / (f_target * 1e6)
    theta = (2 * math.pi * l_wire) / lam_target
    xc = -z0 / math.tan(theta)
    xl = abs(xc)
    return xl / (2 * math.pi * f_target)


def solve_turns(l_target, d_in, p_mm):
    """Solve for number of turns using Wheeler's formula."""
    p_in = p_mm / 25.4
    n = 30.0
    for _ in range(100):
        l_in = n * p_in
        cur_l = (d_in**2 * n**2) / (18 * d_in + 40 * l_in)
        if abs(cur_l - l_target) < 0.01:
            break
        n = n * math.sqrt(l_target / cur_l)
    return math.ceil(n)


def build_coil_former(
    target_freq_mhz: float = 3.65,
    current_res_mhz: float = 7.15,
    velocity_factor: float = 0.96,
    char_impedance_z0: float = 450,
    former_id: float = 57.0,
    wire_copper_dia: float = 1.5,
    insulation_thick: float = 0.15,
    wire_pitch: float = 2.0,
    wall_thickness: float = 3.5,
    clearance_fit: float = 0.5,
    groove_depth_ratio: float = 0.6,
) -> tuple[cq.Workplane, CoilInfo]:
    """Build a parametric inductive coil former."""

    total_wire_dia = wire_copper_dia + (2 * insulation_thick)
    if wire_pitch <= total_wire_dia:
        wire_pitch = total_wire_dia + 0.1

    # RF calculations
    wire_len_m = (C / (current_res_mhz * 1e6)) * 0.25 * velocity_factor
    target_l_uh = calc_inductance(
        target_freq_mhz, wire_len_m, char_impedance_z0, velocity_factor
    )

    # Wheeler's solver
    mean_radius_mm = (former_id + wall_thickness) / 2.0
    mean_diam_in = (mean_radius_mm * 2) / 25.4

    num_turns = solve_turns(target_l_uh, mean_diam_in, wire_pitch)
    coil_height = num_turns * wire_pitch
    total_height = coil_height + 20.0

    # CadQuery geometry
    od = former_id + (wall_thickness * 2)
    former = (
        cq.Workplane("XY")
        .circle(od / 2)
        .extrude(total_height)
        .faces(">Z")
        .workplane()
        .circle((former_id + clearance_fit) / 2)
        .cutThruAll()
    )

    def helix(t):
        angle = 2 * math.pi * num_turns * t
        return (
            mean_radius_mm * math.cos(angle),
            mean_radius_mm * math.sin(angle),
            (t * coil_height) + 10.0,
        )

    path = cq.Workplane("XY").parametricCurve(helix)
    wire_profile = (
        cq.Workplane("XZ")
        .center(
            mean_radius_mm + (total_wire_dia * (0.5 - groove_depth_ratio)),
            10,
        )
        .circle(total_wire_dia / 2)
    )

    former = former.cut(wire_profile.sweep(path, isFrenet=True))

    info = CoilInfo(
        turns=num_turns,
        inductance_uh=target_l_uh,
        wire_length_m=wire_len_m,
        coil_height=coil_height,
        total_height=total_height,
        outer_diameter=od,
        total_wire_dia=total_wire_dia,
    )

    return former, info


def export_step(result: cq.Workplane, output_path: Path) -> None:
    cq.exporters.export(result, str(output_path))


def export_stl(result: cq.Workplane, output_path: Path) -> None:
    cq.exporters.export(result, str(output_path), exportType="STL")
