"""
Blessed Dashboard - Production-Ready Strategy Optimizer TUI
A fully interactive, visually organized terminal UI for real-time monitoring
of crypto strategy optimization with key metrics, backtesting results, and system health.
"""
import logging
import math
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from blessed import Terminal


class BlessedDashboard:
    """Interactive production dashboard with strategy metrics and system health monitoring"""

    def __init__(self):
        self.term = Terminal()
        self.state = {
            "iteration": 0,
            "total_iterations": 10,
            "current_equity": 10000.0,
            "total_pnl": 0.0,
            "pnl_pct": 0.0,
            "max_drawdown": 0.0,
            "open_positions": 0,
            "total_trades": 0,
            "last_signal": 0,  # 1=buy, -1=sell, 0=hold
            "last_price": 0.0,
            "regime": "INITIALIZING",
            "backtest_trades": 0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "audit_verdict": "PENDING",
            "runtime_seconds": 0,
        }
        self.start_time = datetime.now()
        self.colors = {
            "primary": lambda x: self.term.color(33) + x + self.term.normal,  # Blue
            "success": lambda x: self.term.color(46) + x + self.term.normal,  # Green
            "warning": lambda x: self.term.color(226) + x + self.term.normal,  # Yellow
            "danger": lambda x: self.term.color(196) + x + self.term.normal,  # Red
            "info": lambda x: self.term.color(51) + x + self.term.normal,  # Cyan
            "accent": lambda x: self.term.color(141) + x + self.term.normal,  # Magenta
            "header": lambda x: self.term.color(99)
            + x
            + self.term.normal,  # Dark magenta
            "bold": lambda x: self.term.bold(x),
        }

    def update_state(self, **kwargs):
        """Update dashboard state"""
        self.state.update(kwargs)
        self.state["runtime_seconds"] = int(
            (datetime.now() - self.start_time).total_seconds()
        )

    def draw_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str = "",
        content: str = "",
    ):
        """Draw a box with title at position"""
        # Top border
        top = "╭" + "─" * (width - 2) + "╮"
        if title:
            title_str = f"╭─ {title} " + "─" * (width - len(title) - 5) + "╮"
            print(self.term.move(y, x) + title_str)
        else:
            print(self.term.move(y, x) + top)

        # Middle lines
        for i in range(1, height - 1):
            line = "│" + " " * (width - 2) + "│"
            print(self.term.move(y + i, x) + line)

        # Bottom border
        bottom = "╰" + "─" * (width - 2) + "╯"
        print(self.term.move(y + height - 1, x) + bottom)

        # Content
        if content:
            content_lines = content.split("\n")
            for i, line in enumerate(content_lines):
                if i < height - 2:
                    print(self.term.move(y + 1 + i, x + 2) + line[: width - 4])

    def draw_header(self):
        """Draw professional header with system info"""
        print(self.term.home + self.term.clear)

        width = self.term.width
        header_line = "═" * width

        # Top decoration
        print(self.colors["header"](header_line))

        # Title
        title = "STRATEGY OPTIMIZER DASHBOARD"
        spaces = (width - len(title)) // 2
        print(self.colors["primary"](self.colors["bold"](" " * spaces + title)))

        # Subtitle with system info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subtitle = f"Real-time Monitoring | {timestamp}"
        spaces = (width - len(subtitle)) // 2
        print(self.colors["info"](" " * spaces + subtitle))

        # Bottom decoration
        print(self.colors["header"](header_line))
        print()

    def draw_progress_bar(self, current: int, total: int, width: int = 40) -> str:
        """Draw a progress bar"""
        if total == 0:
            return "○" * width

        percent = current / total
        filled = int(width * percent)

        bar = self.colors["success"]("█" * filled) + "░" * (width - filled)
        return bar

    def draw_metric_box(self, title: str, metrics: List[Tuple[str, str, str]]) -> str:
        """Draw a metric box with label-value pairs"""
        lines = [self.colors["bold"](f"╔═ {title}")]

        for label, value, color_fn in metrics:
            value_str = color_fn(value) if callable(color_fn) else value
            line = f"║ {label:<20} {value_str:>15}"
            lines.append(line)

        lines.append("╚" + "═" * 50)
        return "\n".join(lines)

    def get_signal_display(self) -> Tuple[str, str]:
        """Get signal emoji and text"""
        if self.state["last_signal"] == 1:
            return "🟢", "BUY"
        elif self.state["last_signal"] == -1:
            return "🔴", "SELL"
        else:
            return "⚪", "HOLD"

    def render_dashboard(self):
        """Render the full dashboard"""
        print(self.term.home + self.term.clear)

        # Header
        self.draw_header()

        width = self.term.width
        mid = width // 2

        # Left column - Portfolio & Trading
        left_y = 6

        # Portfolio Brew
        equity_color = (
            self.colors["success"]
            if self.state["current_equity"] >= 10000
            else self.colors["danger"]
        )
        pnl_color = (
            self.colors["success"]
            if self.state["total_pnl"] >= 0
            else self.colors["danger"]
        )

        portfolio_metrics = [
            ("EQUITY", f"${self.state['current_equity']:,.0f}", equity_color),
            (
                "P&L",
                f"${self.state['total_pnl']:,.0f} ({self.state['pnl_pct']:.1f}%)",
                pnl_color,
            ),
            (
                "MAX DRAWDOWN",
                f"{self.state['max_drawdown']:.2f}%",
                self.colors["warning"],
            ),
            ("SHARPE RATIO", f"{self.state['sharpe_ratio']:.2f}", self.colors["info"]),
        ]

        portfolio_content = self.draw_metric_box("PORTFOLIO METRICS", portfolio_metrics)
        print(
            self.term.move(left_y, 2)
            + portfolio_content.replace("\n", "\n" + self.term.move(left_y + 1, 2))
        )

        # Trading Activity
        signal_emoji, signal_text = self.get_signal_display()
        signal_color = (
            self.colors["success"]
            if self.state["last_signal"] == 1
            else (
                self.colors["danger"]
                if self.state["last_signal"] == -1
                else self.colors["warning"]
            )
        )

        trading_metrics = [
            ("SIGNAL", f"{signal_emoji} {signal_text}", signal_color),
            ("PRICE", f"${self.state['last_price']:,.2f}", self.colors["accent"]),
            ("REGIME", self.state["regime"], self.colors["info"]),
            (
                "OPEN POSITIONS",
                str(self.state["open_positions"]),
                self.colors["primary"],
            ),
            ("TOTAL TRADES", str(self.state["total_trades"]), self.colors["info"]),
        ]

        trading_content = self.draw_metric_box("TRADING ACTIVITY", trading_metrics)
        left_y += 8
        print(
            self.term.move(left_y, 2)
            + trading_content.replace("\n", "\n" + self.term.move(left_y + 1, 2))
        )

        # Right column - Progress & Metrics
        right_y = 6
        right_x = mid + 2

        # Progress
        progress_pct = (
            self.state["iteration"] / max(self.state["total_iterations"], 1)
        ) * 100
        progress_bar = self.draw_progress_bar(
            self.state["iteration"], self.state["total_iterations"]
        )

        progress_content = f"""╔═ OPTIMIZATION PROGRESS
║ Iteration {self.state['iteration']:>2}/{self.state['total_iterations']:<2}
║ {progress_bar}
║ {progress_pct:.0f}% Complete
╚═══════════════════════════════════════════"""

        print(
            self.term.move(right_y, right_x)
            + progress_content.replace(
                "\n", "\n" + self.term.move(right_y + 1, right_x)
            )
        )

        # Optimization Metrics
        right_y += 7
        win_rate_pct = self.state["win_rate"] * 100
        metrics_content = f"""╔═ BACKTEST METRICS
║ Trades Executed: {self.state['backtest_trades']:>3}
║ Win Rate:        {win_rate_pct:.2f}%
║ Audit Status:    {self.state['audit_verdict']:<10}
║ Runtime:        {self.state['runtime_seconds']:>3}s
╚═══════════════════════════════════════════"""

        print(
            self.term.move(right_y, right_x)
            + metrics_content.replace("\n", "\n" + self.term.move(right_y + 1, right_x))
        )

        # Bottom status bar
        bottom_y = self.term.height - 3
        status_bar = "═" * width
        status_msg = "Press Ctrl+C to exit | System running normally"
        spaces = (width - len(status_msg)) // 2

        print(self.term.move(bottom_y, 0) + self.colors["header"](status_bar))
        print(
            self.term.move(bottom_y + 1, 0)
            + self.colors["info"](" " * spaces + status_msg)
        )
        print(self.term.move(bottom_y + 2, 0) + self.colors["header"](status_bar))

    def print_iteration_banner(self, iteration: int):
        """Print iteration banner"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        banner = f"ITERATION {iteration} - {timestamp}"
        width = self.term.width
        spaces = (width - len(banner)) // 2

        print()
        print(self.colors["primary"](self.colors["bold"](" " * spaces + banner)))
        print(self.colors["header"]("═" * width))
        print()

    def print_signal(self, signal: int, score: float, price: float):
        """Print signal notification"""
        emoji, signal_text = (("🟢", "BUY"), ("🔴", "SELL"), ("⚪", "HOLD"))[
            {1: 0, -1: 1}.get(signal, 2)
        ]

        color_fn = (
            self.colors["success"]
            if signal == 1
            else (self.colors["danger"] if signal == -1 else self.colors["warning"])
        )

        msg = f"{emoji} {signal_text} SIGNAL - Score: {score:.2f}, Price: ${price:,.2f}"
        print(color_fn(self.colors["bold"](msg)))

    def print_trade_executed(self, side: str, amount: float, price: float):
        """Print trade execution notification"""
        emoji = "🟢" if side.upper() == "BUY" else "🔴"
        color_fn = (
            self.colors["success"] if side.upper() == "BUY" else self.colors["danger"]
        )

        msg = f"{emoji} Trade Executed: {side.upper()} {amount:.4f} @ ${price:,.2f}"
        print(color_fn(self.colors["bold"](msg)))

    def print_portfolio_update(
        self, equity: float, pnl: float, drawdown: float, positions: int
    ):
        """Print portfolio update"""
        pnl_color = self.colors["success"] if pnl >= 0 else self.colors["danger"]

        msg = f"💰 Equity: ${equity:,.0f} | P&L: ${pnl:,.0f} | Drawdown: {drawdown:.2f}% | Positions: {positions}"
        print(pnl_color(msg))

    def animate_progress(self, current: int, total: int):
        """Animate progress bar"""
        symbols = ["◜", "◝", "◞", "◟"]
        for i in range(4):
            symbol = symbols[i % len(symbols)]
            bar = self.draw_progress_bar(current, total)
            print(
                f"\r{symbol} Loading {(current/total)*100:.0f}% {bar}",
                end="",
                flush=True,
            )
            time.sleep(0.1)
        print()


# Demo function
def demo_blessed_dashboard():
    """Run demo of blessed dashboard"""
    dashboard = BlessedDashboard()

    # Initial render
    dashboard.render_dashboard()

    # Simulate iterations
    for iteration in range(1, 4):
        time.sleep(1.5)

        dashboard.print_iteration_banner(iteration)

        # Update state with demo data
        dashboard.update_state(
            iteration=iteration,
            backtest_trades=50 + (iteration * 15),
            sharpe_ratio=0.85 + (iteration * 0.1),
            win_rate=0.5 + (iteration * 0.05),
            current_equity=10000 + (iteration * 500),
            total_pnl=iteration * 500,
            pnl_pct=(iteration * 500) / 10000 * 100,
            max_drawdown=5.0 + (iteration * 0.5),
            open_positions=iteration,
            total_trades=iteration * 10,
            regime=["TREND", "HIGH_VOL", "RANGE"][iteration % 3],
        )

        # Print trading events
        print(
            f"Step 1: Running backtest... {dashboard.state['backtest_trades']} trades found"
        )
        time.sleep(0.5)

        print(
            f"Step 2: Extracting metrics... Profit: {dashboard.state['pnl_pct']:.2f}%"
        )
        time.sleep(0.5)

        print(f"Step 3: Classifying regime... {dashboard.state['regime']}")
        time.sleep(0.5)

        dashboard.print_signal(1, 2.2, 83788.48)
        time.sleep(0.3)

        dashboard.print_trade_executed("BUY", 0.067, 83788.48)
        time.sleep(0.3)

        dashboard.print_portfolio_update(
            dashboard.state["current_equity"],
            dashboard.state["total_pnl"],
            dashboard.state["max_drawdown"],
            dashboard.state["open_positions"],
        )

        print()
        time.sleep(1)

        # Re-render dashboard
        dashboard.render_dashboard()

    print(
        "\n"
        + dashboard.colors["success"](
            dashboard.colors["bold"]("Optimization Complete!")
        )
    )
    print()


if __name__ == "__main__":
    demo_blessed_dashboard()
