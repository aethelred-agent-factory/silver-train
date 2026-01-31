import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class CLIDashboard:
    """
    Rich-based CLI dashboard for displaying optimizer state and metrics.
    """

    def __init__(self):
        self.console = Console()
        logging.info("Initialized CLIDashboard.")

    def display_iteration_summary(
        self,
        iteration: int,
        timestamp: str,
        regime: str,
        regime_confidence: float,
        global_metrics: Dict,
        per_regime_metrics: Dict,
        stability_state: str,
        ai_reasoning: Optional[str] = None,
        freeze_countdown: Optional[int] = None,
    ):
        """
        Display a complete iteration summary with all key metrics.
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header"),
            Layout(name="metrics"),
            Layout(name="regimes"),
            Layout(name="stability"),
            Layout(name="ai_decision"),
        )

        # Header
        header_text = f"[bold cyan]Iteration {iteration}[/bold cyan] | [yellow]{timestamp}[/yellow]"
        layout["header"].update(Panel(header_text, style="bold blue"))

        # Global Metrics
        metrics_table = self._build_metrics_table(
            regime, regime_confidence, global_metrics
        )
        layout["metrics"].update(
            Panel(metrics_table, title="[bold]Global Metrics[/bold]")
        )

        # Per-Regime Metrics
        regime_table = self._build_regime_table(per_regime_metrics)
        layout["regimes"].update(
            Panel(regime_table, title="[bold]Per-Regime Performance[/bold]")
        )

        # Stability Info
        stability_text = self._build_stability_text(stability_state, freeze_countdown)
        layout["stability"].update(
            Panel(
                stability_text,
                title="[bold]Stability State[/bold]",
                style="bold yellow" if stability_state != "NORMAL" else "",
            )
        )

        # AI Decision
        if ai_reasoning:
            layout["ai_decision"].update(
                Panel(ai_reasoning, title="[bold]AI Reasoning[/bold]", style="dim")
            )

        self.console.print(layout)

    def _build_metrics_table(
        self, regime: str, confidence: float, metrics: Dict
    ) -> Table:
        """Build the global metrics table."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        regime_style = self._get_regime_style(regime)
        table.add_row(
            f"[{regime_style}]Regime[/{regime_style}]",
            f"[{regime_style}]{regime}[/{regime_style}]",
        )
        table.add_row("Confidence", f"{confidence:.2%}")
        table.add_row(
            "Profit",
            f"[green]{metrics.get('profit', 0):.2f}%[/green]"
            if metrics.get("profit", 0) > 0
            else f"[red]{metrics.get('profit', 0):.2f}%[/red]",
        )
        table.add_row(
            "Max Drawdown", f"[red]{metrics.get('max_drawdown_pct', 0):.2f}%[/red]"
        )
        table.add_row("Win Rate", f"{metrics.get('win_rate', 0):.2f}%")
        table.add_row("Total Trades", str(metrics.get("total_trades", 0)))
        table.add_row("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
        table.add_row("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")

        return table

    def _build_regime_table(self, per_regime_metrics: Dict) -> Table:
        """Build the per-regime metrics table."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Regime", style="cyan")
        table.add_column("Trades", style="yellow")
        table.add_column("Win Rate", style="green")
        table.add_column("Return %", style="cyan")

        for regime, metrics in per_regime_metrics.items():
            regime_style = self._get_regime_style(regime)
            table.add_row(
                f"[{regime_style}]{regime}[/{regime_style}]",
                str(metrics.get("total_trades", 0)),
                f"{metrics.get('win_rate', 0):.2f}%",
                f"{metrics.get('return_pct', 0):.2f}%",
            )

        return table

    def _build_stability_text(
        self, stability_state: str, freeze_countdown: Optional[int]
    ) -> str:
        """Build the stability state text."""
        if stability_state == "FROZEN":
            countdown_text = (
                f" - Frozen for {freeze_countdown} more iterations"
                if freeze_countdown
                else ""
            )
            return f"[bold yellow]⏸  FROZEN{countdown_text}[/bold yellow]\nParameters are locked to ensure stability."
        elif stability_state == "RECOVERY":
            return "[bold red]⚠️  RECOVERY[/bold red]\nRolled back due to drawdown spike. Monitor closely."
        else:
            return "[bold green]✓ NORMAL[/bold green]\nSystem operating normally."

    def _get_regime_style(self, regime: str) -> str:
        """Get the display style for a regime."""
        styles = {
            "TREND": "bold blue",
            "RANGE": "bold cyan",
            "HIGH_VOL": "bold red",
            "UNKNOWN": "dim",
        }
        return styles.get(regime, "dim")

    def display_parameter_update(self, old_params: Dict, new_params: Dict, action: str):
        """
        Display parameter update information.
        """
        table = Table(
            show_header=True,
            header_style="bold magenta",
            title=f"Parameter Update: {action}",
        )
        table.add_column("Parameter", style="cyan")
        table.add_column("Old Value", style="yellow")
        table.add_column("New Value", style="green")

        all_params = set(old_params.keys()) | set(new_params.keys())
        for param in sorted(all_params):
            old_val = old_params.get(param, "N/A")
            new_val = new_params.get(param, "N/A")

            if old_val != new_val:
                change_indicator = "→" if old_val != "N/A" else "+"
                table.add_row(
                    param, str(old_val), f"[green]{change_indicator} {new_val}[/green]"
                )
            else:
                table.add_row(param, str(old_val), str(new_val))

        self.console.print(Panel(table, style="bold green"))

    def display_error(self, error_message: str, title: str = "Error"):
        """
        Display an error message.
        """
        self.console.print(
            Panel(
                f"[bold red]{error_message}[/bold red]",
                title=f"[bold red]{title}[/bold red]",
                style="bold red",
            )
        )

    def display_warning(self, warning_message: str, title: str = "Warning"):
        """
        Display a warning message.
        """
        self.console.print(
            Panel(
                f"[bold yellow]{warning_message}[/bold yellow]",
                title=f"[bold yellow]{title}[/bold yellow]",
                style="bold yellow",
            )
        )

    def display_info(self, info_message: str, title: str = "Info"):
        """
        Display an info message.
        """
        self.console.print(
            Panel(
                info_message, title=f"[bold cyan]{title}[/bold cyan]", style="bold cyan"
            )
        )

    def display_backtest_results(self, backtest_result):
        """
        Display comprehensive backtest results.
        """
        table = Table(
            show_header=True, header_style="bold magenta", title="Backtest Results"
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Start Date", str(backtest_result.start_date))
        table.add_row("End Date", str(backtest_result.end_date))
        table.add_row("Total Trades", str(backtest_result.total_trades))
        table.add_row("Win Rate", f"{backtest_result.win_rate:.2f}%")
        table.add_row("Profit Factor", f"{backtest_result.profit_factor:.2f}")
        table.add_row("Max Drawdown", f"{backtest_result.max_drawdown_pct:.2f}%")
        table.add_row("Sharpe Ratio", f"{backtest_result.sharpe_ratio:.2f}")
        table.add_row("Sortino Ratio", f"{backtest_result.sortino_ratio:.2f}")
        table.add_row("Parameter Hash", backtest_result.parameter_hash)

        self.console.print(Panel(table))

    def display_markdown_report(self, markdown_content: str):
        """
        Display a markdown report.
        """
        from rich.markdown import Markdown

        self.console.print(Markdown(markdown_content))

    def clear(self):
        """Clear the console."""
        self.console.clear()

    def display_table(self, table: Table, title: Optional[str] = None, style: str = ""):
        """
        Display an arbitrary table with optional title.
        """
        if title:
            self.console.print(Panel(table, title=f"[bold]{title}[/bold]", style=style))
        else:
            self.console.print(table)
