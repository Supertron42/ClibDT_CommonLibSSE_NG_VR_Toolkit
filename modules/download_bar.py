from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.console import Console
import requests

def download_with_rich(url, dest_path):
    response = requests.get(url, stream=True)
    total = int(response.headers.get('Content-Length', 0))

    console = Console()
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Downloading", total=total)
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    console.print(f"[green]Download complete! Saved to {dest_path}[/green]")
