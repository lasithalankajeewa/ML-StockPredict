# SmartStock AI: Problem Statement

## Professional motivation and business context

My professional background is in point-of-sale (POS) systems, where I work with
sales data from many merchants. These merchants often operate several outlets.
Some run restaurants, while others run retail stores, but both types of business
must maintain inventory and order items before they are needed. Inventory
planning is therefore a recurring operational problem across the merchants and
outlets represented in POS data.

In practice, merchants often recognize that an item needs replenishment only
when its stock is almost finished or already unavailable. Ordering too late can
cause stockouts, lost sales, interrupted restaurant operations, and dissatisfied
customers. Ordering too much creates a different problem: money is tied up in
stock, more storage space is required, and perishable or time-sensitive items
may be wasted. The business needs a reasonable stock level that protects product
availability without creating unnecessary excess.

Many merchants estimate future demand by looking only at sales from the previous
week. This is a useful and understandable starting point, but it is often not
accurate enough. Demand can change by outlet location, product, weekday, month,
holiday or event, season, selling price, and recent sales pattern. Weather,
promotions, local activity, and supplier conditions may also matter when those
data are available. A useful forecasting system should consider several factors
together instead of assuming that next week will exactly repeat last week.

## Proposed solution

SmartStock AI is a decision-support prototype that turns POS-style sales history
into a seven-day demand forecast for each product-store pair. It combines that
forecast with current stock and a safety-stock target to recommend a reorder
quantity and assign a stock-risk level. The intended user is a merchant,
inventory planner, or outlet manager who needs a prioritized list of products
requiring attention rather than a raw forecast file.

I selected a Deep Neural Network (DNN) because demand is influenced by nonlinear
relationships between numerical history and categorical context. For example,
the same weekday or event can affect different products, categories, stores, and
locations in different ways. The model uses dense layers and categorical
embeddings to learn these interactions. The DNN is still evaluated against a
seasonal naive method and a smaller ANN; it is selected only if validation
results show that it predicts demand more reliably.

The machine-learning task is supervised regression. For a product in one store
on a forecast-origin date, the system predicts total unit demand over the
following seven days. Current inputs include lagged sales, rolling demand
statistics, price behavior, calendar attributes, events, product hierarchy,
store, and state. Weather is identified as a useful future extension because it
is not available in the stored dataset used for this experiment. A forecast is
converted into an inventory recommendation using:

```text
recommended reorder = max(0, predicted 7-day demand + safety stock - current stock)
```

Risk is HIGH when current stock is below predicted demand, MEDIUM when stock
covers predicted demand but not the safety buffer, and LOW when both forecast
demand and safety stock are covered. The model therefore supports a concrete
business action while keeping the forecast visible for human review.

## Data and prediction scope

To represent the multi-outlet environment I encounter in POS work, I use a
stored US multi-location retail sales dataset. It contains hierarchical unit
sales for 3,049 products across ten stores, together with calendar, event, and
weekly selling-price information. The implemented final evaluation covers
30,490 product-store series and 853,720 rolling forecast origins.

SmartStock AI uses a seven-day horizon because weekly replenishment is practical
to present and evaluate in an inventory dashboard. This is an educational
decision-support system, not a production ordering system.

## Modeling objective and validation

The main objective is to improve seven-day demand forecasts over a seasonal
naive baseline that uses the previous seven days of observed demand. Models are
compared with mean absolute error (MAE), root mean squared error (RMSE), and
weighted absolute percentage error (WAPE). WAPE is the primary selection metric
because it summarizes absolute error relative to total observed demand without
the instability of item-level percentage errors when actual demand is zero.

All splits are chronological. A seven-day purge gap separates training from
validation and validation from test because every target contains seven future
days. Model selection and architecture tuning use validation data. The final
test period is opened once after the original DNN has been selected and frozen.
This prevents future-target leakage and prevents test results from influencing
model selection.

## Success criteria

The project is considered successful when it:

1. Builds leakage-safe features for every store without loading the complete
   long-form dataset into memory at once.
2. Beats the seasonal naive baseline on MAE, RMSE, and WAPE on the held-out test
   set.
3. Reports overall, per-store, category, and demand-level errors rather than a
   single headline number.
4. Saves the selected model and fitted preprocessing so inference never refits
   transformations on request data.
5. Exposes a documented API that returns a forecast and inventory decision.
6. Provides a searchable dashboard covering every product-store forecast.
7. Can be installed and run from a fresh clone using documented commands.

The frozen DNN meets the forecasting criterion: test WAPE is 33.64%, compared
with 39.25% for the seasonal naive baseline, a relative reduction of 14.29%.

## Constraints and limitations

The dataset is historical and represents a limited set of US stores, so results
do not automatically generalize to other retailers, countries, or recent market
conditions. Targets from adjacent forecast origins overlap, which makes the
853,720 evaluation rows useful for aggregate comparison but not statistically
independent observations. Forecasts are point estimates and do not quantify
uncertainty.

The stored dataset does not contain live inventory, lead time, supplier
constraints, case-pack sizes, spoilage, or ordering costs. The current-stock
and safety-stock values shown in the dashboard are deterministic demonstration
inputs. A real deployment must connect to an inventory system, validate stock
freshness, incorporate lead times and
service levels, monitor drift, and keep a human approval step for purchasing.
