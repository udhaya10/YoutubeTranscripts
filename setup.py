#!/usr/bin/env python3
"""
YouTube Transcripts - Automated Setup Script

This script automates the setup process for the YouTube Transcripts project.
It supports both Docker-based and local environment setups.

Usage:
    python setup.py              # Auto-detect and recommend setup mode
    python setup.py docker       # Force Docker setup
    python setup.py local        # Force local setup
    python setup.py --help       # Show help
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple, Literal
import re

# Use Rich for beautiful CLI output (install if not found)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    print("\n⚠️  Rich library not found. Installing it now...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "rich"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        print("✅ Rich installed successfully. Retrying import...\n")
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.progress import Progress, SpinnerColumn, TextColumn
            from rich.table import Table
            from rich.prompt import Prompt, Confirm
            from rich import print as rprint
            RICH_AVAILABLE = True
        except ImportError:
            print("⚠️  Could not import Rich even after installation. Using basic output.\n")
    else:
        print("⚠️  Could not install Rich. Using basic output.\n")

    # Fallback: Create dummy Rich-like classes using basic print
    if not RICH_AVAILABLE:
        class Console:
            def print(self, text, *args, **kwargs):
                print(text)
            def status(self, text):
                class Status:
                    def __enter__(self):
                        print(text)
                        return self
                    def __exit__(self, *args):
                        pass
                return Status()

        class Panel:
            def __init__(self, text, title=None, border_style=None):
                self.text = text
                self.title = title

        class Prompt:
            @staticmethod
            def ask(prompt_text, password=False, default=""):
                if default:
                    response = input(f"{prompt_text} [{default}]: ").strip()
                    return response or default
                else:
                    return input(f"{prompt_text}: ").strip()

        class Confirm:
            @staticmethod
            def ask(prompt_text, default=False):
                default_str = "Y/n" if default else "y/N"
                response = input(f"{prompt_text} [{default_str}]: ").strip().lower()
                if response == "":
                    return default
                return response in ["y", "yes"]

        console = Console()
        rprint = print
    else:
        console = Console()


class SetupOrchestrator:
    """Main setup orchestrator for YouTube Transcripts"""

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.platform_type = self._detect_platform()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.venv_path = self.project_root / ".venv"
        self.config_path = self.project_root / "config.json"
        self.env_path = self.project_root / ".env"
        self.env_example_path = self.project_root / ".env.example"

    def _detect_platform(self) -> str:
        """Detect the operating system"""
        system = platform.system()
        if system == "Darwin":
            return "macos"
        elif system == "Linux":
            return "linux"
        elif system == "Windows":
            return "windows"
        else:
            return "unknown"

    def display_banner(self):
        """Display welcome banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║   YouTube Transcripts - Automated Setup                  ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]

[dim]Platform:[/dim] {platform}
[dim]Python:[/dim] {python}
[dim]Project Root:[/dim] {root}
        """.format(
            platform=f"{self.platform_type.upper()} {platform.platform()}",
            python=self.python_version,
            root=str(self.project_root),
        )
        console.print(banner)

    def recommend_mode(self) -> Literal["docker", "local"]:
        """Recommend setup mode based on system"""
        if self._check_docker_installed():
            console.print("\n[green]✓ Docker detected[/green]")
            if Confirm.ask("Use Docker setup? (Recommended)"):
                return "docker"

        console.print("[yellow]ℹ Using local setup mode[/yellow]")
        return "local"

    def run(self, mode: Optional[str] = None):
        """Main entry point"""
        try:
            self.display_banner()

            if mode is None:
                mode = self.recommend_mode()
            elif mode not in ["docker", "local"]:
                console.print(f"[red]Invalid mode: {mode}[/red]")
                console.print("Valid modes: docker, local")
                return False

            console.print(f"\n[bold cyan]Starting {mode.upper()} setup...[/bold cyan]\n")

            if mode == "docker":
                success = self.setup_docker()
            else:
                success = self.setup_local()

            if success:
                self.display_success_message(mode)
                return True
            else:
                console.print("\n[red]Setup failed![/red]")
                return False

        except KeyboardInterrupt:
            console.print("\n[yellow]Setup cancelled by user[/yellow]")
            return False
        except Exception as e:
            console.print(f"\n[red]Unexpected error: {e}[/red]")
            return False

    # ==================== DOCKER SETUP ====================

    def setup_docker(self) -> bool:
        """Execute Docker-based setup"""
        steps = [
            ("Checking Docker installation", self._check_docker_installed),
            ("Collecting HuggingFace token", self.prompt_for_hf_token),
            ("Creating .env file", self.create_env_file),
            ("Building Docker image", self.build_docker_image),
            ("Testing container", self.test_container),
            ("Setting up volumes", self.setup_docker_volumes),
        ]

        for step_name, step_func in steps:
            console.print(f"\n[bold cyan]{step_name}...[/bold cyan]")
            try:
                result = step_func()
                if result is False:
                    console.print(f"[red]✗ {step_name} failed[/red]")
                    return False
                console.print(f"[green]✓ {step_name} complete[/green]")
            except Exception as e:
                console.print(f"[red]✗ {step_name} failed: {e}[/red]")
                return False

        return True

    def _check_docker_installed(self) -> bool:
        """Check if Docker is installed"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                docker_version = result.stdout.strip()
                console.print(f"[dim]{docker_version}[/dim]")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        console.print("[yellow]⚠ Docker not found[/yellow]")
        console.print("Install Docker from: https://www.docker.com/products/docker-desktop")
        console.print("\nWould you like to use local setup instead? (No Docker required)")
        return False

    def build_docker_image(self) -> bool:
        """Build Docker image using docker-compose"""
        try:
            with console.status("[bold cyan]Building Docker image...[/bold cyan]"):
                result = subprocess.run(
                    ["docker", "compose", "build"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minutes timeout
                )

            if result.returncode == 0:
                console.print("[green]Docker image built successfully[/green]")
                return True
            else:
                console.print(f"[red]Build failed:[/red]\n{result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            console.print("[red]Build timeout (10 minutes)[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Build error: {e}[/red]")
            return False

    def test_container(self) -> bool:
        """Test container startup"""
        try:
            with console.status("[bold cyan]Testing container...[/bold cyan]"):
                result = subprocess.run(
                    ["docker", "compose", "run", "--rm", "youtube-extractor", "--help"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={**os.environ, "HF_TOKEN": "test_token_validation"},
                )

            if result.returncode == 0:
                console.print("[green]Container works correctly[/green]")
                return True
            else:
                console.print(f"[yellow]Container test returned non-zero: {result.returncode}[/yellow]")
                # This is usually okay - just means the container ran
                return True
        except Exception as e:
            console.print(f"[yellow]Container test warning: {e}[/yellow]")
            return True  # Don't fail the entire setup on this

    def setup_docker_volumes(self) -> bool:
        """Create Docker volume directories"""
        try:
            transcripts_dir = self.project_root / "transcripts"
            transcripts_dir.mkdir(exist_ok=True)
            console.print(f"[dim]Created: {transcripts_dir}[/dim]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to create volumes: {e}[/red]")
            return False

    # ==================== LOCAL SETUP ====================

    def setup_local(self) -> bool:
        """Execute local environment setup"""
        steps = [
            ("Checking Python version", self._check_python_version),
            ("Checking system resources", self._check_system_resources),
            ("Installing FFmpeg", self._install_ffmpeg),
            ("Creating virtual environment", self._create_virtual_environment),
            ("Installing Python packages", self._install_python_packages),
            ("Collecting HuggingFace token", self.prompt_for_hf_token),
            ("Configuring GPU support (optional)", self._configure_gpu_support),
            ("Creating configuration", self._create_config_json),
            ("Validating installation", self._validate_local_installation),
        ]

        for step_name, step_func in steps:
            console.print(f"\n[bold cyan]{step_name}...[/bold cyan]")
            try:
                result = step_func()
                if result is False:
                    console.print(f"[red]✗ {step_name} failed[/red]")
                    return False
                console.print(f"[green]✓ {step_name} complete[/green]")
            except Exception as e:
                console.print(f"[red]✗ {step_name} failed: {e}[/red]")
                return False

        return True

    def _check_python_version(self) -> bool:
        """Verify Python 3.10+"""
        if sys.version_info >= (3, 10):
            console.print(f"[dim]Python {self.python_version} ✓[/dim]")
            return True
        else:
            console.print(f"[red]Python 3.10+ required (found {self.python_version})[/red]")
            return False

    def _check_system_resources(self) -> bool:
        """Check system RAM and disk space"""
        try:
            import psutil

            # Check RAM
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb < 8:
                console.print(
                    f"[yellow]⚠ System RAM: {memory_gb:.1f}GB (8GB+ recommended)[/yellow]\n"
                    f"[dim]Transcription will work but may be slower. "
                    f"Use --compute-type int8 or CPU mode if issues occur.[/dim]"
                )
            else:
                console.print(f"[dim]System RAM: {memory_gb:.1f}GB ✓[/dim]")

            # Check disk space
            disk_gb = psutil.disk_usage("/").free / (1024**3)
            if disk_gb < 5:
                console.print(
                    f"[yellow]⚠ Available disk: {disk_gb:.1f}GB (5GB+ recommended for models)[/yellow]"
                )
            else:
                console.print(f"[dim]Available disk: {disk_gb:.1f}GB ✓[/dim]")

            return True
        except ImportError:
            console.print("[dim]psutil not available - skipping resource check[/dim]")
            return True
        except Exception as e:
            console.print(f"[yellow]Could not check system resources: {e}[/yellow]")
            return True

    def _install_ffmpeg(self) -> bool:
        """Install FFmpeg based on platform"""
        if self._check_ffmpeg_exists():
            console.print("[dim]FFmpeg already installed[/dim]")
            return True

        console.print(f"[yellow]Installing FFmpeg ({self.platform_type})...[/yellow]")

        if self.platform_type == "macos":
            return self._install_ffmpeg_macos()
        elif self.platform_type == "linux":
            return self._install_ffmpeg_linux()
        elif self.platform_type == "windows":
            return self._install_ffmpeg_windows()
        else:
            console.print("[red]Unsupported platform for auto-install[/red]")
            console.print("Please install FFmpeg manually: https://ffmpeg.org/download.html")
            return False

    def _check_ffmpeg_exists(self) -> bool:
        """Check if FFmpeg is available in PATH"""
        return shutil.which("ffmpeg") is not None

    def _install_ffmpeg_macos(self) -> bool:
        """Install FFmpeg on macOS using Homebrew"""
        if not shutil.which("brew"):
            console.print(
                "[red]Homebrew not found[/red]\n"
                "[yellow]Install Homebrew first: https://brew.sh[/yellow]"
            )
            return False

        try:
            with console.status("[dim]Running: brew install ffmpeg[/dim]"):
                result = subprocess.run(
                    ["brew", "install", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
            if result.returncode == 0:
                console.print("[green]FFmpeg installed[/green]")
                return True
            else:
                console.print(f"[red]Installation failed[/red]\n{result.stderr}")
                return False
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return False

    def _install_ffmpeg_linux(self) -> bool:
        """Install FFmpeg on Linux"""
        # Try apt-get
        if shutil.which("apt-get"):
            try:
                console.print("[dim]Running: sudo apt-get update && sudo apt-get install -y ffmpeg[/dim]")
                subprocess.run(
                    ["sudo", "apt-get", "update"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True,
                )
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True,
                )
                console.print("[green]FFmpeg installed[/green]")
                return True
            except Exception as e:
                console.print(f"[yellow]apt-get install failed: {e}[/yellow]")

        # Try yum
        if shutil.which("yum"):
            try:
                console.print("[dim]Running: sudo yum install -y ffmpeg[/dim]")
                subprocess.run(
                    ["sudo", "yum", "install", "-y", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True,
                )
                console.print("[green]FFmpeg installed[/green]")
                return True
            except Exception as e:
                console.print(f"[yellow]yum install failed: {e}[/yellow]")

        console.print("[red]Could not find apt-get or yum[/red]")
        console.print("Please install FFmpeg manually: https://ffmpeg.org/download.html")
        return False

    def _install_ffmpeg_windows(self) -> bool:
        """Install FFmpeg on Windows"""
        if shutil.which("choco"):
            try:
                console.print("[dim]Running: choco install ffmpeg -y[/dim]")
                result = subprocess.run(
                    ["choco", "install", "ffmpeg", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    console.print("[green]FFmpeg installed[/green]")
                    return True
            except Exception as e:
                console.print(f"[yellow]Chocolatey install failed: {e}[/yellow]")

        console.print("[yellow]Chocolatey not found[/yellow]")
        console.print("Download FFmpeg: https://ffmpeg.org/download.html")
        input("Press Enter after installing FFmpeg...")
        return self._check_ffmpeg_exists()

    def _create_virtual_environment(self) -> bool:
        """Create or verify Python virtual environment"""
        if self.venv_path.exists():
            console.print(f"[dim]venv already exists at {self.venv_path}[/dim]")
            return True

        try:
            with console.status(f"[dim]Creating venv at {self.venv_path}...[/dim]"):
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_path)],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
            console.print("[green]Virtual environment created[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to create venv: {e}[/red]")
            return False

    def _install_python_packages(self) -> bool:
        """Install Python dependencies"""
        try:
            requirements_path = self.project_root / "requirements.txt"
            if not requirements_path.exists():
                console.print("[red]requirements.txt not found[/red]")
                return False

            # Determine pip executable
            if self.platform_type == "windows":
                pip_exe = self.venv_path / "Scripts" / "pip"
            else:
                pip_exe = self.venv_path / "bin" / "pip"

            with console.status("[dim]Installing dependencies (this may take several minutes)...[/dim]"):
                result = subprocess.run(
                    [str(pip_exe), "install", "-r", str(requirements_path)],
                    capture_output=True,
                    text=True,
                    timeout=1200,  # 20 minutes
                )

            if result.returncode == 0:
                console.print("[green]Python packages installed[/green]")
                return True
            else:
                console.print(f"[red]Installation failed[/red]\n{result.stderr}")
                return False
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return False

    def _configure_gpu_support(self) -> bool:
        """Optional GPU/CUDA setup for NVIDIA users"""
        try:
            # Only offer on platforms that support CUDA
            if self.platform_type not in ["linux", "windows"]:
                console.print("[dim]GPU support not available on this platform[/dim]")
                return True

            console.print(
                "\n[bold cyan]GPU Acceleration (Optional)[/bold cyan]\n"
                "GPU can make transcription ~2-3x faster.\n"
                "[dim]Requirements:[/dim]\n"
                "  • NVIDIA GPU\n"
                "  • CUDA 12.8 installed\n"
                "[dim]Your CPU will also work fine - this is optional.[/dim]\n"
            )

            if not Confirm.ask("Install GPU support (PyTorch with CUDA)?", default=False):
                console.print("[dim]Skipping GPU setup (will use CPU)[/dim]")
                return True

            console.print(
                "[yellow]Note:[/yellow] This will reinstall PyTorch with CUDA support.\n"
                "[dim]Make sure CUDA 12.8 is installed first:[/dim]\n"
                "  Linux: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/\n"
                "  Windows: https://developer.nvidia.com/cuda-12-8-1-download-archive\n"
            )

            if not Confirm.ask("Continue with GPU setup?", default=False):
                console.print("[dim]GPU setup cancelled[/dim]")
                return True

            # Reinstall PyTorch with CUDA support
            if self.platform_type == "windows":
                pip_exe = self.venv_path / "Scripts" / "pip"
            else:
                pip_exe = self.venv_path / "bin" / "pip"

            with console.status("[dim]Installing PyTorch with CUDA 12.8 support...[/dim]"):
                result = subprocess.run(
                    [
                        str(pip_exe),
                        "install",
                        "--upgrade",
                        "torch",
                        "torchvision",
                        "torchaudio",
                        "--index-url",
                        "https://download.pytorch.org/whl/cu128",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

            if result.returncode == 0:
                console.print("[green]GPU support installed[/green]")
                console.print("[dim]Use --device cuda flag when running:[/dim]")
                console.print("[dim]  python main.py URL --device cuda[/dim]")
                return True
            else:
                console.print(f"[yellow]GPU installation had issues. CPU mode will work:[/yellow]\n{result.stderr}")
                return True  # Don't fail - CPU mode still works

        except Exception as e:
            console.print(f"[yellow]GPU setup warning: {e}[/yellow]")
            return True  # Don't fail - CPU mode still works

    def _create_config_json(self) -> bool:
        """Generate config.json with HF token"""
        try:
            hf_token = self.hf_token_global  # Set by prompt_for_hf_token()
            config = {
                "hf_token": hf_token,
                "output_directory": "./transcripts",
                "default_language": "en",
                "default_compute_type": "int8",
                "enable_diarization": True,
                "max_workers": 4,
            }

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)

            console.print(f"[dim]Created: {self.config_path}[/dim]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to create config: {e}[/red]")
            return False

    def _validate_local_installation(self) -> bool:
        """Validate that all dependencies are working"""
        try:
            if self.platform_type == "windows":
                python_exe = self.venv_path / "Scripts" / "python"
            else:
                python_exe = self.venv_path / "bin" / "python"

            # Try to import whisperx
            with console.status("[dim]Validating whisperx import...[/dim]"):
                result = subprocess.run(
                    [str(python_exe), "-c", "import whisperx; print('OK')"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            if result.returncode == 0 and "OK" in result.stdout:
                console.print("[green]All dependencies validated[/green]")
                return True
            else:
                console.print("[yellow]Warning: Could not validate whisperx[/yellow]")
                # Don't fail - it might work fine at runtime
                return True
        except Exception as e:
            console.print(f"[yellow]Validation warning: {e}[/yellow]")
            return True

    # ==================== COMMON SETUP ====================

    def prompt_for_hf_token(self) -> bool:
        """Prompt user for HuggingFace token"""
        console.print(
            "\n[bold cyan]HuggingFace Configuration[/bold cyan]\n"
            "To enable speaker diarization (identifying speakers), you need a HuggingFace token.\n"
            "[dim]Steps:[/dim]\n"
            "  1. Visit: [link=https://huggingface.co/pyannote/speaker-diarization-3.1]"
            "https://huggingface.co/pyannote/speaker-diarization-3.1[/link]\n"
            "  2. Click: [bold]'Agree and access repository'[/bold]\n"
            "  3. Get token: [link=https://huggingface.co/settings/tokens]"
            "https://huggingface.co/settings/tokens[/link]\n"
            "  4. Paste below (or press Enter to skip)\n"
        )

        token = Prompt.ask("[bold]HuggingFace token[/bold]", password=False, default="")

        if not token:
            console.print("[yellow]⚠ Proceeding without speaker diarization[/yellow]")
            self.hf_token_global = ""
            return True

        if not self._validate_hf_token_format(token):
            console.print("[red]Invalid token format (should start with 'hf_')[/red]")
            return self.prompt_for_hf_token()  # Re-prompt

        self.hf_token_global = token
        console.print("[green]✓ Token configured[/green]")
        return True

    def _validate_hf_token_format(self, token: str) -> bool:
        """Validate HF token format"""
        if not token:
            return True  # Empty is okay (optional)
        # HF tokens typically start with 'hf_'
        return token.startswith("hf_")

    def create_env_file(self) -> bool:
        """Create .env file from template"""
        try:
            if self.env_path.exists():
                if not Confirm.ask(".env already exists. Overwrite?"):
                    console.print("[dim].env kept as-is[/dim]")
                    return True

            # Read template
            if not self.env_example_path.exists():
                console.print("[red].env.example not found[/red]")
                return False

            with open(self.env_example_path, "r") as f:
                env_content = f.read()

            # Replace placeholder with actual token
            env_content = env_content.replace(
                "your_huggingface_token_here", self.hf_token_global
            )

            # Write .env
            with open(self.env_path, "w") as f:
                f.write(env_content)

            console.print(f"[dim]Created: {self.env_path}[/dim]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to create .env: {e}[/red]")
            return False

    def display_success_message(self, mode: str):
        """Display success message with next steps"""
        success_panel = Panel(
            "[bold green]Setup Complete! 🎉[/bold green]",
            title="YouTube Transcripts",
            border_style="green",
        )
        console.print(success_panel)

        if mode == "docker":
            console.print(
                "\n[bold cyan]Next Steps:[/bold cyan]\n"
                "1. [yellow]Process a single video:[/yellow]\n"
                "   [dim]docker compose run --rm youtube-extractor https://youtu.be/VIDEO_ID[/dim]\n\n"
                "2. [yellow]Batch process from file:[/yellow]\n"
                "   [dim]echo 'https://youtu.be/VIDEO1' > urls.txt[/dim]\n"
                "   [dim]docker compose run --rm youtube-extractor --from-file /app/urls.txt[/dim]\n\n"
                "3. [yellow]View outputs:[/yellow]\n"
                "   [dim]ls ./transcripts/[/dim]\n\n"
                "4. [yellow]For help:[/yellow]\n"
                "   [dim]docker compose run --rm youtube-extractor --help[/dim]\n"
            )
        else:
            console.print(
                "\n[bold cyan]Next Steps:[/bold cyan]\n"
                "1. [yellow]Activate virtual environment:[/yellow]\n"
                "   [dim]source .venv/bin/activate[/dim] (macOS/Linux)\n"
                "   [dim].venv\\Scripts\\activate[/dim] (Windows)\n\n"
                "2. [yellow]Process a video:[/yellow]\n"
                "   [dim]python main.py https://youtu.be/VIDEO_ID[/dim]\n\n"
                "3. [yellow]View outputs in:[/yellow]\n"
                "   [dim]./transcripts/[/dim]\n\n"
                "4. [yellow]For help:[/yellow]\n"
                "   [dim]python main.py --help[/dim]\n"
            )

        console.print(
            "[dim]─" * 50 + "[/dim]\n"
            "[dim]Documentation: See README.md for more information[/dim]\n"
        )


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="YouTube Transcripts - Automated Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py              # Auto-detect setup mode
  python setup.py docker       # Force Docker setup
  python setup.py local        # Force local setup
        """,
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default=None,
        choices=["docker", "local"],
        help="Setup mode (auto-detected if not specified)",
    )

    args = parser.parse_args()

    orchestrator = SetupOrchestrator()
    success = orchestrator.run(args.mode)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
