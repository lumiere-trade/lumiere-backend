#!/usr/bin/env python3
"""
Update port configuration from ports.yaml (Single Source of Truth).

Reads ports.yaml and updates only port-related fields in:
- Component YAML configs (*.yaml)
- Preserves all other settings
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


class PortUpdater:
    """Update port-related configuration from ports.yaml SSOT."""

    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root_dir = root_dir
        self.dry_run = dry_run
        self.ports_file = root_dir / "ports.yaml"
        self.ports_config: Dict[str, Any] = {}
        self.changes_made = False

    def load_ports_config(self) -> None:
        """Load and validate ports.yaml."""
        if not self.ports_file.exists():
            raise FileNotFoundError(f"ports.yaml not found at {self.ports_file}")

        with open(self.ports_file, "r") as f:
            self.ports_config = yaml.safe_load(f)

        print(f"[OK] Loaded {self.ports_file}")

    def update_component_yaml(
        self, component: str, environment: str, config_file: Path
    ) -> None:
        """Update port-related fields in component YAML config."""
        if not config_file.exists():
            print(f"[SKIP] {config_file} does not exist")
            return

        # Load existing config
        with open(config_file, "r") as f:
            existing_config = yaml.safe_load(f) or {}

        # Get ports from ports.yaml
        env_config = self.ports_config["environments"][environment]
        component_config = env_config[component]

        # Get service discovery URLs
        sd_config = self.ports_config["service_discovery"][environment]

        # Prepare updates based on component type
        updates = {}

        if component == "pourtier":
            # Main API
            updates["API_PORT"] = component_config["api_port"]

            # Monitoring ports
            updates["METRICS_ENABLED"] = True
            updates["METRICS_HOST"] = "0.0.0.0"
            updates["METRICS_PORT"] = component_config["metrics_port"]

            updates["HEALTH_CHECK_ENABLED"] = True
            updates["HEALTH_HOST"] = "0.0.0.0"
            updates["HEALTH_PORT"] = component_config["health_port"]

            # Service discovery
            updates["COURIER_URL"] = sd_config.get("courier")
            updates["PASSEUR_URL"] = sd_config.get("passeur")

            # Remove old fields
            if "HEALTH_CHECK_PORT" in existing_config:
                del existing_config["HEALTH_CHECK_PORT"]

        elif component == "courier":
            updates["port"] = component_config["api_port"]
            updates["pourtier_url"] = sd_config.get("pourtier")
            updates["passeur_url"] = sd_config.get("passeur")

        elif component == "passeur":
            updates["bridge_port"] = component_config["api_port"]
            updates["courier_url"] = sd_config.get("courier")
            updates["pourtier_url"] = sd_config.get("pourtier")

        # Check if any values changed
        changed = False
        changes = []

        for key, new_value in updates.items():
            old_value = existing_config.get(key)
            if old_value != new_value:
                changed = True
                changes.append(f"  {key}: {old_value} -> {new_value}")
                if not self.dry_run:
                    existing_config[key] = new_value

        if not changed:
            print(f"[OK] {config_file.name} (no changes)")
            return

        if self.dry_run:
            print(f"[CHANGE] {config_file}")
            for change in changes:
                print(change)
        else:
            # Write updated config
            with open(config_file, "w") as f:
                yaml.dump(
                    existing_config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            print(f"[UPDATED] {config_file.name}")
            self.changes_made = True

    def update_all_component_configs(self) -> None:
        """Update all component YAML configs."""
        print("\n=== Updating Component Configs ===")

        components = ["pourtier", "courier", "passeur"]
        environments = ["production", "development"]

        for component in components:
            print(f"\n{component.upper()}:")
            for environment in environments:
                config_file = (
                    self.root_dir / component / "config" / f"{environment}.yaml"
                )
                self.update_component_yaml(component, environment, config_file)

    def check_consistency(self) -> bool:
        """Check if all configs match ports.yaml."""
        print("\n=== Checking Port Consistency ===")

        components = ["pourtier", "courier", "passeur"]
        environments = ["production", "development"]
        all_consistent = True

        for component in components:
            for environment in environments:
                config_file = (
                    self.root_dir / component / "config" / f"{environment}.yaml"
                )

                if not config_file.exists():
                    print(f"[MISSING] {config_file}")
                    all_consistent = False
                    continue

                with open(config_file, "r") as f:
                    existing_config = yaml.safe_load(f) or {}

                env_config = self.ports_config["environments"][environment]
                component_config = env_config[component]

                # Check API port
                if component == "pourtier":
                    expected_port = component_config["api_port"]
                    actual_port = existing_config.get("API_PORT")

                    if actual_port != expected_port:
                        print(
                            f"[MISMATCH] {component}/{environment}: "
                            f"API_PORT={actual_port}, expected {expected_port}"
                        )
                        all_consistent = False

                    # Check monitoring ports for pourtier
                    expected_metrics = component_config["metrics_port"]
                    actual_metrics = existing_config.get("METRICS_PORT")

                    if actual_metrics != expected_metrics:
                        print(
                            f"[MISMATCH] {component}/{environment}: "
                            f"METRICS_PORT={actual_metrics}, expected {expected_metrics}"
                        )
                        all_consistent = False

                    expected_health = component_config["health_port"]
                    actual_health = existing_config.get("HEALTH_PORT")

                    if actual_health != expected_health:
                        print(
                            f"[MISMATCH] {component}/{environment}: "
                            f"HEALTH_PORT={actual_health}, expected {expected_health}"
                        )
                        all_consistent = False

                elif component == "courier":
                    expected_port = component_config["api_port"]
                    actual_port = existing_config.get("port")

                    if actual_port != expected_port:
                        print(
                            f"[MISMATCH] {component}/{environment}: "
                            f"port={actual_port}, expected {expected_port}"
                        )
                        all_consistent = False

                elif component == "passeur":
                    expected_port = component_config["api_port"]
                    actual_port = existing_config.get("bridge_port")

                    if actual_port != expected_port:
                        print(
                            f"[MISMATCH] {component}/{environment}: "
                            f"bridge_port={actual_port}, expected {expected_port}"
                        )
                        all_consistent = False

        if all_consistent:
            print("\n[OK] All configurations consistent with ports.yaml")
        else:
            print("\n[ERROR] Mismatches found. Run: python scripts/update_ports.py")

        return all_consistent

    def run(self, check_only: bool = False) -> None:
        """Run the updater."""
        print("=" * 60)
        print("Lumiere Port Configuration Updater")
        print("=" * 60)

        self.load_ports_config()

        if check_only:
            consistent = self.check_consistency()
            sys.exit(0 if consistent else 1)

        self.update_all_component_configs()

        print("\n" + "=" * 60)
        if self.dry_run:
            print("DRY RUN - No files modified")
        elif self.changes_made:
            print("COMPLETE - Files updated")
            print("\nVerify: git diff */config/*.yaml")
        else:
            print("NO CHANGES - All configs already consistent")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update port configuration from ports.yaml"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check consistency only",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    updater = PortUpdater(project_root, dry_run=args.dry_run)

    try:
        updater.run(check_only=args.check)
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
