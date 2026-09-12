# SmartStock AI: Problem Statement

## Business context

Retail inventory decisions require a balance between product availability and
working-capital efficiency. If a store holds too little stock, customers face
stockouts and the retailer loses sales. If it holds too much, cash remains tied
up in inventory and the business incurs additional storage, handling, and
markdown costs. These decisions are difficult when thousands of products have
different demand levels, seasonal patterns, event effects, prices, and local
store behavior.

SmartStock AI is a decision-support prototype that turns recent sales history
into a seven-day demand forecast for each product-store pair. It then combines
the forecast with current stock and a safety-stock target to recommend a reorder
quantity and assign a stock-risk level. The intended user is an inventory
planner or store manager who needs a short, prioritized list of items requiring
attention rather than a raw forecast file.

## Problem being solved

The machine-learning problem is supervised regression. For a product in one
store on a forecast-origin date, the system predicts total unit demand over the
following seven days. Inputs include lagged sales, rolling demand statistics,
price behavior, calendar attributes, events, product hierarchy, store, and
state. A forecast is converted into an inventory recommendation using:

```text
recommended reorder = max(0, predicted 7-day demand + safety stock - current stock)
```

Risk is HIGH when current stock is below predicted demand, MEDIUM when stock
covers predicted demand but not the safety buffer, and LOW when both forecast
demand and safety stock are covered. The model therefore supports a concrete
business action while keeping the forecast visible for human review.

## Data and prediction scope

The project uses the M5 Forecasting - Accuracy dataset, which contains
hierarchical Walmart unit-sales data for 3,049 products sold across ten stores
in California, Texas, and Wisconsin. Calendar, event, SNAP, and weekly selling
price data provide explanatory variables. The implemented final evaluation
covers 30,490 product-store series and 853,720 rolling forecast origins.

The original M5 competition used a 28-day objective. SmartStock AI intentionally
uses a seven-day horizon because weekly replenishment is easier to present and
evaluate in an inventory dashboard. This is an educational decision-support
system, not a production ordering system.

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

The M5 data is historical and represents a limited set of US stores, so results
do not automatically generalize to other retailers, countries, or recent market
conditions. Targets from adjacent forecast origins overlap, which makes the
853,720 evaluation rows useful for aggregate comparison but not statistically
independent observations. Forecasts are point estimates and do not quantify
uncertainty.

M5 does not contain live inventory, lead time, supplier constraints, case-pack
sizes, spoilage, or ordering costs. Dashboard current-stock and safety-stock
values are deterministic demonstration inputs. A real deployment must connect
to an inventory system, validate stock freshness, incorporate lead times and
service levels, monitor drift, and keep a human approval step for purchasing.
