"""
Drata Kong Tests - Main Entry Point

Runs all compliance tests against Kong Gateway and pushes evidence to Drata.

Usage:
    python -m src.main                    # Run all tests
    python -m src.main --dry-run          # Run without pushing to Drata
    python -m src.main --verbose          # Verbose output
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import List

from rich.console import Console
from rich.table import Table

from .config import load_config, Config
from .clients.kong import KonnectClient, DataplaneClient
from .clients.drata import DrataClient, DrataMockClient, DrataEvidencePayload
from .tests.base import Evidence
from .tests.runtime import (
    RT001_RateLimitFreeTier,
    RT002_RateLimitProTier,
    RT003_InvalidKeyRejected,
    RT004_MissingKeyRejected,
    RT005_ValidKeyAccepted,
    RT006_ConsumerIdentityInjected,
)
from .tests.configuration import (
    CF001_AuthPluginEnabled,
    CF002_RateLimitPluginEnabled,
    CF003_AllConsumersHaveLimits,
)


console = Console()


def create_tests(config: Config, konnect: KonnectClient, dataplane: DataplaneClient):
    """Create all test instances."""
    return [
        # Runtime tests
        RT001_RateLimitFreeTier(dataplane, config.kong.free_trial_key),
        RT002_RateLimitProTier(dataplane, config.kong.pro_key),
        RT003_InvalidKeyRejected(dataplane),
        RT004_MissingKeyRejected(dataplane),
        RT005_ValidKeyAccepted(dataplane, config.kong.pro_key),
        RT006_ConsumerIdentityInjected(
            dataplane, 
            config.kong.pro_key, 
            "tier_pro"
        ),
        # Configuration tests
        CF001_AuthPluginEnabled(konnect),
        CF002_RateLimitPluginEnabled(konnect),
        CF003_AllConsumersHaveLimits(konnect),
    ]


def run_tests(tests, verbose: bool = False) -> List[Evidence]:
    """Run all tests and collect evidence."""
    results = []
    
    console.print("\n[bold blue]Running Compliance Tests[/bold blue]\n")
    
    for test in tests:
        console.print(f"  Running {test.test_id}: {test.test_name}...", end=" ")
        
        evidence = test.run()
        results.append(evidence)
        
        if evidence.result == "PASS":
            console.print("[green]PASS[/green]")
        elif evidence.result == "FAIL":
            console.print("[red]FAIL[/red]")
        else:
            console.print(f"[yellow]{evidence.result}[/yellow]")
        
        if verbose and evidence.error_message:
            console.print(f"    [red]Error: {evidence.error_message}[/red]")
    
    return results


def print_summary(results: List[Evidence]):
    """Print a summary table of test results."""
    table = Table(title="Test Results Summary")
    table.add_column("Test ID", style="cyan")
    table.add_column("Test Name")
    table.add_column("Result")
    table.add_column("Duration")
    table.add_column("Controls")
    
    for evidence in results:
        result_style = {
            "PASS": "green",
            "FAIL": "red",
            "ERROR": "yellow",
            "SKIP": "dim",
        }.get(evidence.result, "white")
        
        table.add_row(
            evidence.test_id,
            evidence.test_name[:40] + "..." if len(evidence.test_name) > 40 else evidence.test_name,
            f"[{result_style}]{evidence.result}[/{result_style}]",
            f"{evidence.duration_ms}ms",
            ", ".join(evidence.control_mapping[:3]),
        )
    
    console.print("\n")
    console.print(table)
    
    # Summary stats
    total = len(results)
    passed = sum(1 for r in results if r.result == "PASS")
    failed = sum(1 for r in results if r.result == "FAIL")
    errors = sum(1 for r in results if r.result == "ERROR")
    
    console.print(f"\n[bold]Total: {total}[/bold] | ", end="")
    console.print(f"[green]Passed: {passed}[/green] | ", end="")
    console.print(f"[red]Failed: {failed}[/red] | ", end="")
    console.print(f"[yellow]Errors: {errors}[/yellow]\n")


def push_to_drata(results: List[Evidence], drata_client, dry_run: bool = False):
    """Push test results to Drata as evidence."""
    console.print("\n[bold blue]Pushing Evidence to Drata[/bold blue]\n")
    
    if dry_run:
        console.print("  [yellow]DRY-RUN mode - not pushing to Drata[/yellow]\n")
    
    for evidence in results:
        # Create Drata evidence payload
        payload = DrataEvidencePayload(
            test_id=evidence.test_id,
            test_name=evidence.test_name,
            result=evidence.result,
            timestamp=evidence.timestamp,
            control_ids=evidence.control_mapping,
            details=evidence.details,
            artifacts=evidence.artifacts,
        )
        
        try:
            # For now, we'll use a mock monitor ID
            # In production, you'd map test_id -> Drata monitor_id
            monitor_id = f"kong-{evidence.test_id.lower()}"
            
            if dry_run:
                console.print(f"  [dim]Would push {evidence.test_id} to monitor {monitor_id}[/dim]")
            else:
                drata_client.submit_external_evidence(monitor_id, payload)
                console.print(f"  [green]Pushed {evidence.test_id}[/green]")
        except Exception as e:
            console.print(f"  [red]Failed to push {evidence.test_id}: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(description="Run Kong compliance tests for Drata")
    parser.add_argument("--dry-run", action="store_true", help="Don't push to Drata")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=str, help="Write results to JSON file")
    args = parser.parse_args()

    console.print("[bold]Drata Kong Tests[/bold]")
    console.print(f"Started at: {datetime.now(timezone.utc).isoformat()}\n")

    # Load configuration
    try:
        config = load_config()
    except KeyError as e:
        console.print(f"[red]Missing required environment variable: {e}[/red]")
        console.print("\nRequired variables:")
        console.print("  KONNECT_TOKEN, DATAPLANE_URL, DRATA_API_KEY")
        sys.exit(1)

    # Override with CLI flags
    if args.dry_run:
        config = Config(
            kong=config.kong,
            drata=config.drata,
            gcp=config.gcp,
            dry_run=True,
            verbose=args.verbose or config.verbose,
        )

    # Initialize clients
    console.print("[dim]Initializing clients...[/dim]")
    
    konnect = KonnectClient(
        token=config.kong.konnect_token,
        api_base=config.kong.konnect_api_base,
        control_plane_name=config.kong.control_plane_name,
    )
    
    dataplane = DataplaneClient(base_url=config.kong.dataplane_url)
    
    if config.dry_run:
        drata = DrataMockClient(verbose=config.verbose)
    else:
        drata = DrataClient(
            api_key=config.drata.api_key,
            api_base=config.drata.api_base,
        )

    # Create and run tests
    tests = create_tests(config, konnect, dataplane)
    results = run_tests(tests, verbose=config.verbose)

    # Print summary
    print_summary(results)

    # Push to Drata
    push_to_drata(results, drata, dry_run=config.dry_run)

    # Write results to file if requested
    if args.output:
        output_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [e.to_dict() for e in results],
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        console.print(f"\n[green]Results written to {args.output}[/green]")

    # Exit with error if any tests failed
    failed_count = sum(1 for r in results if r.result in ["FAIL", "ERROR"])
    if failed_count > 0:
        console.print(f"\n[red]Exiting with error: {failed_count} test(s) failed[/red]")
        sys.exit(1)
    
    console.print("\n[green]All tests passed![/green]")
    sys.exit(0)


if __name__ == "__main__":
    main()

