"""
main.py

Beautiful CLI interface for YouTube Knowledge Base Extractor.
Built with Typer and Rich for stunning terminal UI.

Usage:
    python main.py https://www.youtube.com/watch?v=VIDEO_ID
    python main.py --from-file urls.txt
    python main.py --help
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import track, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.syntax import Syntax

from youtube_extractor import (
    YouTubeExtractor,
    YouTubeLinkDetector,
    MetadataExtractor,
    ProcessingResult,
)

# ============================================================================
# SETUP AND CONFIGURATION
# ============================================================================

# Rich Console for beautiful terminal output
console = Console()

# Application metadata
APP_NAME = "🎥 YouTube Knowledge Base Extractor"
APP_VERSION = "1.0.0"
CONFIG_FILE = Path("config.json")
DEFAULT_OUTPUT_DIR = Path("./transcripts")
DEFAULT_LOG_DIR = Path("./logs")

# Typer CLI app
app = typer.Typer(
    help="Extract transcripts and metadata from YouTube videos with speaker diarization.",
    no_args_is_help=True,
)


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class AppConfig:
    """Manages application configuration"""

    @staticmethod
    def load() -> dict:
        """Load configuration from config.json"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {
            "hf_token": None,
            "output_directory": str(DEFAULT_OUTPUT_DIR),
            "default_language": "en",
            "default_compute_type": "int8",
            "enable_diarization": True,
            "max_workers": 4,
        }

    @staticmethod
    def save(config: dict):
        """Save configuration to config.json"""
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def setup_first_run():
        """Interactive first-run setup"""
        console.print(
            Panel(
                f"[bold cyan]{APP_NAME}[/bold cyan]\n[dim]v{APP_VERSION}[/dim]",
                expand=False,
                border_style="cyan",
            )
        )

        console.print(
            "\n[bold yellow]⚙️  First Run Setup[/bold yellow]\n"
            "[dim]Configure your extraction preferences below.[/dim]\n"
        )

        # HuggingFace Token (required for diarization)
        hf_token = typer.prompt(
            "[bold]📌 HuggingFace Token[/bold] (for speaker diarization)",
            default="",
            hide_input=False,
        )

        if not hf_token:
            console.print(
                "[yellow]⚠️  Warning: Skipping HuggingFace token. Speaker diarization will be disabled.[/yellow]"
            )

        # Output directory
        output_dir = typer.prompt(
            "[bold]📂 Output Directory[/bold] (where to save transcripts)",
            default=str(DEFAULT_OUTPUT_DIR),
        )

        # Language
        language = typer.prompt(
            "[bold]🗣️  Language[/bold] (transcription language code, e.g., 'en' for English)",
            default="en",
        )

        # Compute type
        console.print("\n[bold]⚙️  Compute Type[/bold]")
        console.print("  [dim]int8[/dim]      - Quantized (faster, less accurate)")
        console.print("  [dim]float32[/dim]   - Full precision (slower, most accurate)")
        console.print("  [dim]float16[/dim]   - Half precision (balanced)")

        compute_type = typer.prompt(
            "Choose compute type", default="int8", type=str
        )

        # Diarization preference
        enable_diarization = typer.confirm(
            "[bold]🎤 Enable Speaker Diarization?[/bold] (detects who is speaking)",
            default=True,
        )

        # Save configuration
        config = {
            "hf_token": hf_token or None,
            "output_directory": output_dir,
            "default_language": language,
            "default_compute_type": compute_type,
            "enable_diarization": enable_diarization and bool(hf_token),
            "max_workers": 4,
        }

        AppConfig.save(config)

        console.print(
            Panel(
                "[bold green]✅ Configuration saved![/bold green]",
                expand=False,
                border_style="green",
            )
        )


# ============================================================================
# BEAUTIFUL DISPLAY HELPERS
# ============================================================================

def display_header():
    """Display application header"""
    console.print(
        Align.center(
            Panel(
                f"[bold cyan]{APP_NAME}[/bold cyan]\n[dim]Extract YouTube Knowledge[/dim]",
                expand=False,
                border_style="cyan",
                padding=(1, 2),
            )
        )
    )


def display_link_info(url: str):
    """Display parsed link information"""
    link_info = YouTubeLinkDetector.detect(url)

    if not link_info.valid:
        console.print(
            f"[bold red]❌ Invalid URL:[/bold red] {url}\n"
            "[dim]Please provide a valid YouTube URL.[/dim]"
        )
        return None

    # Create a nice table for link info
    table = Table(title="🔍 Link Detection", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("URL", link_info.url)
    table.add_row(
        "Type",
        f"[bold]{link_info.link_type}[/bold]"
        if link_info.link_type != "INVALID"
        else "[bold red]INVALID[/bold red]",
    )

    if link_info.video_id:
        table.add_row("Video ID", link_info.video_id)
    if link_info.playlist_id:
        table.add_row("Playlist ID", link_info.playlist_id)
    if link_info.channel_id:
        table.add_row("Channel ID", link_info.channel_id)

    console.print(table)
    return link_info


def display_metadata(metadata):
    """Display video metadata in a beautiful format"""
    if not metadata:
        return

    # Convert duration to HH:MM:SS
    duration_seconds = metadata.duration_seconds
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60

    duration_str = (
        f"{hours}h {minutes}m {seconds}s"
        if hours > 0
        else f"{minutes}m {seconds}s"
    )

    # Create metadata panel
    metadata_text = (
        f"[bold cyan]Title:[/bold cyan] {metadata.title}\n"
        f"[bold cyan]Channel:[/bold cyan] {metadata.channel}\n"
        f"[bold cyan]Duration:[/bold cyan] {duration_str}\n"
        f"[bold cyan]Views:[/bold cyan] {metadata.view_count:,}\n"
        f"[bold cyan]Uploaded:[/bold cyan] {metadata.upload_date}\n"
        f"[bold cyan]Available Captions:[/bold cyan] {', '.join(metadata.available_subtitles) or 'None'}\n"
        f"[bold cyan]Auto-Generated Captions:[/bold cyan] {', '.join(metadata.available_auto_captions) or 'None'}"
    )

    console.print(Panel(metadata_text, title="📊 Video Metadata", expand=False))


def display_processing_results(results: List[ProcessingResult]):
    """Display processing results in a summary table"""
    table = Table(title="📋 Processing Summary")
    table.add_column("Video ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="magenta")
    table.add_column("Time (s)", style="yellow")
    table.add_column("Error", style="red")

    for result in results:
        status_symbol = (
            "✅ Success" if result.status == "success" else f"❌ {result.status.upper()}"
        )

        error_msg = result.error_message[:40] + "..." if result.error_message else "-"

        table.add_row(
            result.video_id[:8] + "...",
            result.title[:30],
            status_symbol,
            f"{result.processing_time_seconds:.1f}",
            error_msg,
        )

    console.print(table)


def display_output_summary(results: List[ProcessingResult]):
    """Display final summary with file paths"""
    successful = [r for r in results if r.status == "success"]

    if not successful:
        console.print("[yellow]⚠️  No videos were successfully processed.[/yellow]")
        return

    console.print(
        Panel(
            "[bold green]🎉 Processing Complete![/bold green]",
            border_style="green",
            expand=False,
        )
    )

    # Create file location table
    table = Table(title="📁 Output Files", show_header=True)
    table.add_column("Video", style="cyan")
    table.add_column("Output Directory", style="green")

    for result in successful:
        table.add_row(result.title[:30], result.output_dir)

    console.print(table)

    # Show overall statistics
    total_duration = sum(r.processing_time_seconds for r in successful)
    console.print(
        f"\n[bold cyan]📊 Summary:[/bold cyan] {len(successful)} videos processed in {total_duration:.1f} seconds"
    )


# ============================================================================
# MAIN COMMAND: PROCESS VIDEOS
# ============================================================================

@app.command()
def process(
    urls: Optional[List[str]] = typer.Argument(
        None, help="YouTube URLs to process"
    ),
    from_file: Optional[Path] = typer.Option(
        None, "--from-file", help="Read URLs from a text file (one per line)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", help="Output directory for transcripts"
    ),
    language: str = typer.Option(
        "en", "--language", help="Language code for transcription (default: en)"
    ),
    compute_type: str = typer.Option(
        "int8", "--compute-type", help="Compute type: int8, float32, float16"
    ),
    no_diarize: bool = typer.Option(
        False, "--no-diarize", help="Disable speaker diarization"
    ),
    device: str = typer.Option(
        "auto", "--device", help="Device: auto, cpu, mps, cuda"
    ),
):
    """
    Process YouTube videos: extract metadata and generate transcripts.

    Examples:
        python main.py https://youtu.be/dQw4w9WgXcQ
        python main.py --from-file urls.txt --output-dir ./my_transcripts
        python main.py URL1 URL2 URL3 --no-diarize
    """

    # Display header
    display_header()

    # Load or create configuration
    config = AppConfig.load()

    # First-run setup check
    if not config.get("hf_token") and not no_diarize:
        console.print(
            "[yellow]⚠️  No HuggingFace token configured. Running first-time setup...[/yellow]\n"
        )
        AppConfig.setup_first_run()
        config = AppConfig.load()

    # Collect URLs
    all_urls = []

    if from_file:
        if not from_file.exists():
            console.print(f"[red]❌ File not found: {from_file}[/red]")
            raise typer.Exit(code=1)

        with open(from_file, "r") as f:
            all_urls = [line.strip() for line in f if line.strip()]

    if urls:
        all_urls.extend(urls)

    if not all_urls:
        console.print(
            "[red]❌ No URLs provided. Use:\n"
            "   python main.py URL\n"
            "   python main.py --from-file urls.txt[/red]"
        )
        raise typer.Exit(code=1)

    console.print(
        f"\n[bold cyan]📌 Found {len(all_urls)} URL(s) to process[/bold cyan]\n"
    )

    # Step 1: Validate and display all URLs
    console.print("[bold yellow]🔍 Link Detection Phase[/bold yellow]\n")

    valid_urls = []
    for i, url in enumerate(all_urls, 1):
        console.print(f"[dim]Processing {i}/{len(all_urls)}...[/dim]")
        link_info = display_link_info(url)
        if link_info and link_info.valid:
            valid_urls.append(url)
        console.print()

    if not valid_urls:
        console.print("[red]❌ No valid YouTube URLs found.[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]✅ {len(valid_urls)} valid URL(s) to process[/green]\n")

    # Step 2: Metadata extraction
    console.print("[bold yellow]📊 Metadata Extraction Phase[/bold yellow]\n")

    metadata_map = {}
    for i, url in enumerate(valid_urls, 1):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                f"[cyan]Extracting metadata ({i}/{len(valid_urls)})...", total=None
            )
            link_info = YouTubeLinkDetector.detect(url)
            metadata = MetadataExtractor.extract(url)

            if metadata and link_info:
                metadata_map[link_info.video_id] = metadata
                display_metadata(metadata)

    console.print(
        f"\n[green]✅ Extracted metadata for {len(metadata_map)} video(s)[/green]\n"
    )

    # Step 3: Processing phase
    console.print("[bold yellow]⚙️  Processing Phase[/bold yellow]\n")

    # Determine output directory
    final_output_dir = output_dir or Path(config.get("output_directory", DEFAULT_OUTPUT_DIR))

    # Initialize extractor
    extractor = YouTubeExtractor(
        output_base_dir=str(final_output_dir),
        language=language or config.get("default_language", "en"),
        compute_type=compute_type or config.get("default_compute_type", "int8"),
        enable_diarization=not no_diarize and config.get("enable_diarization", True),
        hf_token=config.get("hf_token"),
    )

    # Process each URL
    results = []
    for i, url in enumerate(valid_urls, 1):
        console.print(
            f"\n[bold cyan]Processing Video {i}/{len(valid_urls)}[/bold cyan]"
        )
        console.print(f"[dim]{url}[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Processing video...", total=None)
            result = extractor.process_video(url)
            results.append(result)

            if result.status == "success":
                console.print(
                    f"[green]✅ Success! ({result.processing_time_seconds:.1f}s)[/green]"
                )
                console.print(f"[dim]Output: {result.output_dir}[/dim]")
            else:
                console.print(
                    f"[red]❌ {result.status.upper()}: {result.error_message}[/red]"
                )

    # Step 4: Summary
    console.print("\n" + "=" * 80)
    display_processing_results(results)
    display_output_summary(results)

    console.print(
        Panel(
            "[bold green]✨ Done![/bold green]\n"
            "[dim]All transcripts have been saved with speaker labels and timestamps.[/dim]",
            border_style="green",
            expand=False,
        )
    )


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@app.command()
def setup():
    """Run interactive setup to configure HuggingFace token and preferences."""
    display_header()
    AppConfig.setup_first_run()


@app.command()
def version():
    """Display application version."""
    console.print(f"[bold cyan]{APP_NAME}[/bold cyan] v[bold yellow]{APP_VERSION}[/bold yellow]")


@app.command()
def config():
    """Display current configuration."""
    display_header()
    current_config = AppConfig.load()

    # Hide sensitive token
    display_config = current_config.copy()
    if display_config.get("hf_token"):
        token = display_config["hf_token"]
        display_config["hf_token"] = token[:10] + "..." if len(token) > 10 else "***"

    syntax = Syntax(
        json.dumps(display_config, indent=2),
        "json",
        theme="monokai",
        line_numbers=False,
    )

    console.print(Panel(syntax, title="⚙️  Current Configuration"))


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected error: {str(e)}[/bold red]")
        raise typer.Exit(code=1)
