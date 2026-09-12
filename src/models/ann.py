"""Keras architecture for the numerical-feature ANN experiment."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def build_ann(
    number_of_features: int,
    *,
    hidden_units: Sequence[int] = (64, 32),
    learning_rate: float = 0.001,
) -> Any:
    """Build and compile the ANN used as the neural-network baseline."""
    if number_of_features <= 0:
        raise ValueError("number_of_features must be positive.")
    if not hidden_units or any(units <= 0 for units in hidden_units):
        raise ValueError("hidden_units must contain positive layer sizes.")

    from tensorflow import keras
    from tensorflow.keras import layers

    model = keras.Sequential(name="smartstock_ann")
    model.add(layers.Input(shape=(number_of_features,), name="numerical"))
    for units in hidden_units:
        model.add(layers.Dense(units, activation="relu"))
    model.add(layers.Dense(1, activation="softplus", name="demand_7d"))
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.Huber(),
        metrics=[keras.metrics.MeanAbsoluteError(name="mae")],
    )
    return model
