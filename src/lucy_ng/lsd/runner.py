"""LSD (Logic for Structure Determination) runner."""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from lucy_ng.lsd.generator import LSDInputGenerator
from lucy_ng.lsd.models import LSDProblem


@dataclass
class LSDResult:
    """Result from LSD execution.

    Attributes:
        success: Whether LSD completed successfully
        solution_count: Number of solutions found
        solutions: List of solution file contents
        output_files: Paths to generated output files
        stdout: Standard output from LSD
        stderr: Standard error from LSD
        return_code: Process return code
        input_file: Path to the input file used
        output_dir: Directory containing output files
    """

    success: bool
    solution_count: int
    solutions: list[str] = field(default_factory=list)
    output_files: list[Path] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    input_file: Path | None = None
    output_dir: Path | None = None

    def summary(self) -> str:
        """Return a summary of the result."""
        status = "Success" if self.success else "Failed"
        lines = [
            f"LSD Result: {status}",
            f"  Solutions found: {self.solution_count}",
            f"  Return code: {self.return_code}",
        ]
        if self.output_files:
            lines.append(f"  Output files: {len(self.output_files)}")
        if self.stderr and not self.success:
            lines.append(f"  Error: {self.stderr[:200]}")
        return "\n".join(lines)


class LSDRunner:
    """Execute LSD solver.

    Manages execution of the LSD program as a subprocess,
    handling input file creation and output file parsing.

    After LSD runs successfully, automatically runs outlsd to convert
    solutions to SMILES format for downstream ranking.
    """

    # Common locations to search for LSD
    SEARCH_PATHS = [
        "/usr/local/bin/lsd",
        "/usr/bin/lsd",
        "~/.local/bin/lsd",
        "~/bin/lsd",  # Common user bin directory
        "~/LSD/lsd",
        "~/PyLSD/LSD/lsd",
        "~/LSD-3.5.3/lsd",  # Default extraction location
    ]

    # Common locations for outlsd
    OUTLSD_SEARCH_PATHS = [
        "/usr/local/bin/outlsd",
        "/usr/bin/outlsd",
        "~/.local/bin/outlsd",
        "~/bin/outlsd",
        "~/LSD/outlsd",
        "~/PyLSD/LSD/outlsd",
        "~/LSD-3.5.3/outlsd",
    ]

    def __init__(self, lsd_path: str | Path | None = None):
        """Initialize with path to LSD executable.

        Args:
            lsd_path: Path to LSD executable. If None, will search
                     in PATH and common locations.
        """
        if lsd_path:
            self.lsd_path = Path(lsd_path).expanduser()
        else:
            self.lsd_path = self._find_lsd()
        self.outlsd_path = self._find_outlsd()

    def run(
        self,
        problem: LSDProblem,
        output_dir: Path | None = None,
        timeout: int = 60,
        keep_files: bool = False,
    ) -> LSDResult:
        """Run LSD on problem and return results.

        Args:
            problem: LSD problem to solve
            output_dir: Directory for output files. If None, uses temp dir.
            timeout: Maximum execution time in seconds
            keep_files: If True, don't clean up temp files

        Returns:
            LSDResult with solution information

        Raises:
            FileNotFoundError: If LSD executable not found
            RuntimeError: If LSD execution fails critically
        """
        if self.lsd_path is None:
            raise FileNotFoundError(
                "LSD executable not found. Install LSD or provide path."
            )

        # Create output directory
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            cleanup = False
        else:
            output_dir = Path(tempfile.mkdtemp(prefix="lsd_"))
            cleanup = not keep_files

        try:
            # Write input file
            input_file = output_dir / f"{problem.name}.lsd"
            LSDInputGenerator.write_file(problem, input_file)

            # Run LSD
            result = self._execute_lsd(input_file, output_dir, timeout)
            result.input_file = input_file
            result.output_dir = output_dir

            return result

        finally:
            if cleanup and output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)

    def run_file(
        self,
        input_file: Path | str,
        output_dir: Path | None = None,
        timeout: int = 60,
    ) -> LSDResult:
        """Run LSD on an existing input file.

        Args:
            input_file: Path to LSD input file
            output_dir: Directory for output files
            timeout: Maximum execution time in seconds

        Returns:
            LSDResult with solution information
        """
        if self.lsd_path is None:
            raise FileNotFoundError(
                "LSD executable not found. Install LSD or provide path."
            )

        input_file = Path(input_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if output_dir is None:
            output_dir = input_file.parent

        result = self._execute_lsd(input_file, output_dir, timeout)
        result.input_file = input_file
        result.output_dir = output_dir

        return result

    def _execute_lsd(
        self,
        input_file: Path,
        output_dir: Path,
        timeout: int,
    ) -> LSDResult:
        """Execute LSD subprocess.

        Args:
            input_file: Path to input file
            output_dir: Working directory
            timeout: Timeout in seconds

        Returns:
            LSDResult with execution information
        """
        try:
            # LSD command: lsd < input.lsd
            proc = subprocess.run(
                [str(self.lsd_path)],
                input=input_file.read_text(),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=output_dir,
            )

            # Find output files
            output_files = list(output_dir.glob("*.sol")) + list(output_dir.glob("*.out"))

            # Count solutions from output (check both stdout and stderr)
            solution_count = self._count_solutions(proc.stdout, output_files, proc.stderr)

            # Read solution contents
            solutions = []
            for sol_file in sorted(output_dir.glob("*.sol")):
                solutions.append(sol_file.read_text())

            # Success if return code is 0 OR if solutions were found
            success = proc.returncode == 0 or solution_count > 0

            # Run outlsd to convert solutions to SMILES if available
            if success and solution_count > 0 and self.outlsd_path:
                self._run_outlsd(output_dir, input_file)
                # Re-scan for output files to include outlsd.out
                output_files = list(output_dir.glob("*.sol")) + list(output_dir.glob("*.out"))

            return LSDResult(
                success=success,
                solution_count=solution_count,
                solutions=solutions,
                output_files=output_files,
                stdout=proc.stdout,
                stderr=proc.stderr,
                return_code=proc.returncode,
            )

        except subprocess.TimeoutExpired:
            return LSDResult(
                success=False,
                solution_count=0,
                stderr=f"LSD execution timed out after {timeout} seconds",
                return_code=-1,
            )

        except Exception as e:
            return LSDResult(
                success=False,
                solution_count=0,
                stderr=str(e),
                return_code=-1,
            )

    def _count_solutions(
        self, stdout: str, output_files: list[Path], stderr: str = ""
    ) -> int:
        """Count number of solutions from LSD output.

        Args:
            stdout: LSD standard output
            output_files: List of output files
            stderr: LSD standard error (LSD often writes here)

        Returns:
            Number of solutions found
        """
        import re

        # Try to parse from stdout and stderr (LSD writes to stderr)
        for text in [stdout, stderr]:
            for line in text.split("\n"):
                if "solution" in line.lower():
                    # Try to extract number
                    match = re.search(r"(\d+)\s+solution", line.lower())
                    if match:
                        return int(match.group(1))

        # Fallback: count .sol files
        sol_files = [f for f in output_files if f.suffix == ".sol"]
        return len(sol_files)

    @classmethod
    def _find_lsd(cls) -> Path | None:
        """Try to find LSD executable.

        Returns:
            Path to LSD executable, or None if not found
        """
        # Check PATH first
        lsd_in_path = shutil.which("lsd")
        if lsd_in_path:
            return Path(lsd_in_path)

        # Check common locations
        for path_str in cls.SEARCH_PATHS:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_file():
                return path

        return None

    @classmethod
    def _find_outlsd(cls) -> Path | None:
        """Try to find outlsd executable for SMILES conversion.

        Returns:
            Path to outlsd executable, or None if not found
        """
        # Check PATH first
        outlsd_in_path = shutil.which("outlsd")
        if outlsd_in_path:
            return Path(outlsd_in_path)

        # Check common locations
        for path_str in cls.OUTLSD_SEARCH_PATHS:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_file():
                return path

        return None

    def _run_outlsd(self, output_dir: Path, input_file: Path) -> None:
        """Run outlsd to convert solutions to SMILES.

        Creates outlsd.out file with SMILES for each solution.

        Args:
            output_dir: Directory containing solution files
            input_file: Original LSD input file
        """
        if self.outlsd_path is None:
            return

        try:
            # outlsd reads from stdin like lsd
            proc = subprocess.run(
                [str(self.outlsd_path)],
                input=input_file.read_text(),
                capture_output=True,
                text=True,
                timeout=30,
                cwd=output_dir,
            )

            # Write output to outlsd.out
            if proc.stdout.strip():
                outlsd_file = output_dir / "outlsd.out"
                outlsd_file.write_text(proc.stdout)

        except Exception:
            # Non-fatal - ranking will just skip solutions without SMILES
            pass

    @classmethod
    def is_available(cls) -> bool:
        """Check if LSD is available on the system.

        Returns:
            True if LSD executable is found
        """
        return cls._find_lsd() is not None

    @classmethod
    def is_outlsd_available(cls) -> bool:
        """Check if outlsd (SMILES converter) is available.

        Returns:
            True if outlsd executable is found
        """
        return cls._find_outlsd() is not None

    @classmethod
    def get_version(cls) -> str | None:
        """Get LSD version if available.

        Returns:
            Version string, or None if not available
        """
        lsd_path = cls._find_lsd()
        if lsd_path is None:
            return None

        try:
            # Try running lsd --version or similar
            result = subprocess.run(
                [str(lsd_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return "unknown"
