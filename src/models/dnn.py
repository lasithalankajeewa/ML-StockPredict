"""Mixed numerical/categorical DNN used by SmartStock experiments."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


def embedding_size(cardinality: int) -> int:
    """Return the bounded embedding width used in the experiment notebook."""
    if cardinality <= 0:
        raise ValueError("Categorical cardinality must be positive.")
    return min(32, max(2, math.ceil(math.sqrt(cardinality + 1))))


def build_dnn(
    number_of_numerical_features: int,
    category_cardinalities: Mapping[str, int],
    *,
    hidden_units: Sequence[int] = (256, 128, 64),
    dropout_rate: float = 0.20,
    learning_rate: float = 0.001,
) -> Any:
    """Build and compile the mixed-input seven-day demand model."""
    if number_of_numerical_features <= 0:
        raise ValueError("number_of_numerical_features must be positive.")
    if not category_cardinalities:
        raise ValueError("At least one categorical feature is required.")
    if not hidden_units or any(units <= 0 for units in hidden_units):
        raise ValueError("hidden_units must contain positive layer sizes.")
    if not 0 <= dropout_rate < 1:
        raise ValueError("dropout_rate must be between zero and one.")

    from tensorflow import keras
    from tensorflow.keras import layers

    numerical = keras.Input(
        shape=(number_of_numerical_features,), name="numerical"
    )
    inputs: dict[str, Any] = {"numerical": numerical}
    encoded = [numerical]

    for name, cardinality in category_cardinalities.items():
        if cardinality <= 0:
            raise ValueError(f"Cardinality for {name!r} must be positive.")
        categorical = keras.Input(shape=(1,), dtype="int32", name=name)
        inputs[name] = categorical
        embedding = layers.Embedding(
            input_dim=cardinality + 2,
            output_dim=embedding_size(cardinality),
            name=f"{name}_embedding",
        )(categorical)
        encoded.append(layers.Flatten()(embedding))

    x = layers.Concatenate()(encoded)
    for units in hidden_units:
        x = layers.Dense(units, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(dropout_rate)(x)

    output = layers.Dense(1, activation="softplus", name="demand_7d")(x)
    model = keras.Model(inputs=inputs, outputs=output, name="smartstock_dnn")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.Huber(),
        metrics=[keras.metrics.MeanAbsoluteError(name="mae")],
    )
    return model
