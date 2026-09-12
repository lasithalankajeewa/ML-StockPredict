"""Named DNN configurations evaluated in the experiment notebook."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DNNConfig:
    """One controlled architecture experiment."""

    name: str
    hidden_units: tuple[int, ...]
    dropout_rate: float
    learning_rate: float


DNN_CONFIGS = (
    DNNConfig("DNN A - Small", (128, 64), 0.15, 0.001),
    DNNConfig("DNN B - Balanced", (256, 128, 64), 0.20, 0.001),
    DNNConfig("DNN C - Wide", (512, 256, 128), 0.25, 0.0005),
    DNNConfig("DNN D - Deep", (256, 128, 64, 32), 0.20, 0.0005),
    DNNConfig("DNN E - Regularized", (512, 256, 128, 64), 0.35, 0.0005),
)


def main() -> None:
    """Print the reproducible tuning matrix used by the notebook."""
    for config in DNN_CONFIGS:
        layers = " -> ".join(map(str, config.hidden_units))
        print(
            f"{config.name}: layers={layers}, dropout={config.dropout_rate}, "
            f"learning_rate={config.learning_rate}"
        )


if __name__ == "__main__":
    main()
