import asyncio
import argparse
import sys
import os

# Set UTF-8 for console output
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from app.models.database import init_db
from app.api.simulator_api import run_scenario, SCENARIOS
from app.ledger.roi_engine import ROIEngine
from app.ledger.audit_ledger import AuditLedgerService

console = Console(highlight=False)


async def run_cli_demo(scenario_keys):
    console.print(Panel.fit(
        "[bold cyan]AI REVENUE RECOVERY SYSTEM -- E2E SIMULATOR[/bold cyan]\n"
        "[dim]LangGraph Reasoning Agent * Policy Guardrails * Action Layer * Immutable Ledger[/dim]",
        border_style="cyan"
    ))

    # Initialize DB
    await init_db()

    for idx, key in enumerate(scenario_keys, 1):
        console.print(f"\n[bold yellow]=== Running Scenario {idx}/{len(scenario_keys)}: [{key.upper()}] ===[/bold yellow]")
        result = await run_scenario(key)
        
        # Display Execution Tree
        tree = Tree(f"[bold white]Case ID: {result.get('case_id')}[/bold white] | Status: [green]{result.get('status')}[/green]")
        
        risk_branch = tree.add(f"[bold magenta]1. Risk Detected:[/bold magenta] {result.get('risk_type')} (Severity: {result.get('severity')}) - ${result.get('amount')} {result.get('currency')}")
        
        diag = result.get("diagnosis", {})
        if diag:
            diag_branch = tree.add(f"[bold blue]2. Diagnosis & Strategy:[/bold blue] {diag.get('strategy_summary')}")
            diag_branch.add(f"Root Cause: [italic]{diag.get('root_cause')}[/italic]")
            diag_branch.add(f"Channel: [bold]{diag.get('recommended_channel')}[/bold]")
            if diag.get("retry_delay_hours"):
                diag_branch.add(f"Smart Retry Window: {diag.get('retry_delay_hours')} hours")
            if diag.get("offered_discount_pct"):
                diag_branch.add(f"Dynamic Incentive: {diag.get('offered_discount_pct')}% OFF")

        guard = result.get("guardrail_result", {})
        if guard:
            is_comp = guard.get("is_compliant")
            color = "green" if is_comp else "red"
            guard_branch = tree.add(f"[bold {color}]3. Policy Guardrails:[/bold {color}] {'PASS (Compliant)' if is_comp else 'BLOCKED'}")
            for v in guard.get("violations", []):
                guard_branch.add(f"[{'red' if v['severity'] == 'block' else 'yellow'}]{v['rule_name']}: {v['message']}[/]")

        act = result.get("action_result", {})
        if act:
            act_branch = tree.add(f"[bold green]4. Action Dispatched:[/bold green] {act.get('channel')} (Status: {act.get('status')})")
            act_branch.add(f"Ref ID: {act.get('external_reference_id')}")
            act_branch.add(f"Operational Cost: ${act.get('cost_usd'):.4f}")

        ledger_seq = result.get("audit_sequence_id")
        tree.add(f"[bold cyan]5. Financial Ledger:[/bold cyan] Sequence #{ledger_seq} Logged with Net ROI Attribution")

        console.print(tree)

    # Print Summary ROI Table
    metrics = await ROIEngine.get_summary_metrics()
    
    table = Table(title="\nFinancial ROI & Recovery Attribution Ledger Summary", border_style="green")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold green")

    table.add_row("Total Revenue at Risk", f"${metrics.total_revenue_at_risk:,.2f}")
    table.add_row("Total Gross Recovered", f"${metrics.total_recovered_revenue:,.2f}")
    table.add_row("Total Operational Costs", f"${metrics.total_recovery_costs:,.4f}")
    table.add_row("Net Recovered Revenue", f"${metrics.net_recovered_revenue:,.2f}")
    table.add_row("Overall Recovery Rate", f"{metrics.overall_recovery_rate_pct}%")
    table.add_row("Net ROI Multiple", f"{metrics.net_roi_multiple}x")
    table.add_row("Cases Processed", str(metrics.total_cases_processed))

    console.print(table)

    # Verify Cryptographic Chain
    verification = await AuditLedgerService.verify_chain_integrity()
    if verification.get("is_valid"):
        console.print(f"[bold green]✓ Cryptographic Audit Chain Validated:[/bold green] {verification.get('total_records_verified')} blocks linked with SHA-256 integrity.")
    else:
        console.print(f"[bold red]✗ Cryptographic Audit Chain Invalid:[/bold red] {verification.get('error')}")


def main():
    parser = argparse.ArgumentParser(description="AI Revenue Recovery System CLI Simulator")
    parser.add_argument(
        "--scenarios",
        default="all",
        choices=["all", "soft_decline", "abandoned_checkout", "overdue_b2b_hinglish", "active_dispute_blocked"],
        help="Scenario(s) to simulate"
    )
    args = parser.parse_args()

    scenario_list = list(SCENARIOS.keys()) if args.scenarios == "all" else [args.scenarios]
    asyncio.run(run_cli_demo(scenario_list))


if __name__ == "__main__":
    main()
