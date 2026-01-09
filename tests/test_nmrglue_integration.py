"""Integration tests for nmrglue library.

These tests verify that nmrglue is properly installed and has the
expected API for Bruker file reading that we'll use in Phase 2.
"""

import pytest


class TestNmrgluAvailability:
    """Tests that nmrglue is available and has expected modules."""

    def test_import_nmrglue(self) -> None:
        """Test that nmrglue can be imported."""
        import nmrglue

        assert nmrglue is not None

    def test_bruker_module_exists(self) -> None:
        """Test that nmrglue.bruker module exists."""
        import nmrglue

        assert hasattr(nmrglue, "bruker")

    def test_bruker_read_functions(self) -> None:
        """Test that Bruker read functions are available."""
        from nmrglue import bruker

        # These are the key functions we'll use in Phase 2
        assert hasattr(bruker, "read")  # Read processed data
        assert hasattr(bruker, "read_pdata")  # Read processed data (alternative)
        assert hasattr(bruker, "read_binary")  # Read raw FID

    def test_process_module_exists(self) -> None:
        """Test that nmrglue.process module exists for peak picking."""
        import nmrglue

        assert hasattr(nmrglue, "process")

    def test_peak_picking_available(self) -> None:
        """Test that peak picking functionality is available."""
        from nmrglue import analysis

        # Peak picking is in the analysis module
        assert hasattr(analysis, "peakpick")


class TestNmrglueBrukerAPI:
    """Document expected nmrglue Bruker API for Phase 2."""

    def test_documented_api(self) -> None:
        """Document the Bruker API we'll use.

        This test serves as documentation of the expected nmrglue API.
        We'll use these functions in Phase 2 for Bruker file reading:

        1D Reading:
            dic, data = nmrglue.bruker.read(dir)
            - dic: dictionary with acquisition parameters
            - data: numpy array with spectrum data

        2D Reading:
            dic, data = nmrglue.bruker.read(dir)
            - dic: dictionary with acquisition parameters (acqu, acqu2s)
            - data: 2D numpy array

        Parameter access:
            dic['acqus']['SFO1']  # Spectrometer frequency
            dic['acqus']['NUC1']  # Nucleus

        PPM scale calculation (nmrglue >= 0.10):
            udic = nmrglue.bruker.guess_udic(dic, data)
            uc = nmrglue.fileiobase.uc_from_udic(udic, dim=0)
            ppm_scale = uc.ppm_scale()
        """
        from nmrglue import bruker, fileiobase

        # Verify guess_udic exists for universal dictionary generation
        assert hasattr(bruker, "guess_udic")
        # Verify uc_from_udic exists for unit conversion
        assert hasattr(fileiobase, "uc_from_udic")
