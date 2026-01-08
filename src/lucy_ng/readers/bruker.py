"""Bruker NMR file reader."""

from pathlib import Path
from typing import Any

import nmrglue as ng
import numpy as np

from lucy_ng.models import Spectrum1D


def _strip_brackets(value: str) -> str:
    """Strip angle brackets from Bruker parameter strings."""
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    return value


def _get_param(dic: dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a parameter from acqus dictionary."""
    try:
        value = dic["acqus"][key]
        if isinstance(value, str):
            return _strip_brackets(value)
        return value
    except KeyError:
        return default


class BrukerReader:
    """Reader for Bruker NMR data files."""

    @staticmethod
    def read_1d(experiment_dir: str | Path) -> Spectrum1D:
        """Read a Bruker 1D experiment directory and return Spectrum1D.

        Args:
            experiment_dir: Path to Bruker experiment directory (contains acqus, pdata/)

        Returns:
            Spectrum1D object with processed data and parameters

        Raises:
            FileNotFoundError: If experiment directory doesn't exist
            ValueError: If nucleus is not supported
        """
        experiment_dir = Path(experiment_dir)

        if not experiment_dir.exists():
            raise FileNotFoundError(f"Experiment directory not found: {experiment_dir}")

        # Read processed data from pdata/1/
        pdata_dir = experiment_dir / "pdata" / "1"
        dic, data = ng.bruker.read_pdata(str(pdata_dir))

        # Also read acqus for acquisition parameters
        acqus_dic, _ = ng.bruker.read(str(experiment_dir))
        dic.update(acqus_dic)

        # Extract parameters
        nucleus = _get_param(dic, "NUC1")
        if nucleus is None:
            raise ValueError("NUC1 parameter not found in acqus")

        frequency = _get_param(dic, "SFO1")
        if frequency is None:
            raise ValueError("SFO1 parameter not found in acqus")

        solvent = _get_param(dic, "SOLVENT")
        pulse_program = _get_param(dic, "PULPROG")
        num_scans = _get_param(dic, "NS")
        temperature = _get_param(dic, "TE")

        # Generate ppm scale
        uc = ng.bruker.make_uc(dic, data)
        ppm_scale = uc.ppm_scale()

        # Build metadata
        metadata: dict[str, Any] = {}
        if pulse_program:
            metadata["pulse_program"] = pulse_program
        if num_scans is not None:
            metadata["num_scans"] = num_scans
        if temperature is not None:
            metadata["temperature"] = temperature

        return Spectrum1D(
            data=np.array(data, dtype=np.float64),
            ppm_scale=np.array(ppm_scale, dtype=np.float64),
            nucleus=nucleus,
            frequency=float(frequency),
            solvent=solvent,
            metadata=metadata,
        )
