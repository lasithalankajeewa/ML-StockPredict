"use client";

import { useMemo, useState } from "react";

import { initialProducts, type Product, type Risk } from "@/lib/dashboard-data";

type ApiResult = {
  predictedDemand7Days: number;
  recommendedReorder: number;
  riskLevel: "HIGH" | "MEDIUM" | "LOW";
};

const riskLabel: Record<ApiResult["riskLevel"], Risk> = {
  HIGH: "High",
  MEDIUM: "Watch",
  LOW: "Healthy",
};

function Icon({ name }: { name: "alert" | "chart" | "box" | "target" | "search" }) {
  const paths = {
    alert: <><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.7 2.4 17.4A2 2 0 0 0 4.1 20h15.8a2 2 0 0 0 1.7-2.6L13.7 3.7a2 2 0 0 0-3.4 0Z"/></>,
    chart: <><path d="M4 19V9"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M22 19H2"/></>,
    box: <><path d="m21 8-9 5-9-5"/><path d="M3 8l9-5 9 5v10l-9 5-9-5Z"/><path d="M12 13v10"/></>,
    target: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v2M21 12h-2M12 21v-2M3 12h2"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>;
}

function MetricCard({ label, value, note, icon, tone = "plain" }: {
  label: string; value: string; note: string;
  icon: "alert" | "chart" | "box" | "target"; tone?: "plain" | "accent";
}) {
  return (
    <article className={`metric-card ${tone === "accent" ? "metric-accent" : ""}`}>
      <div className="metric-top"><span>{label}</span><span className="metric-icon"><Icon name={icon}/></span></div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

function RiskBadge({ risk }: { risk: Risk }) {
  return <span className={`risk-badge risk-${risk.toLowerCase()}`}><i />{risk}</span>;
}

function DemandChart({ product }: { product: Product }) {
  const width = 720;
  const height = 236;
  const pad = 22;
  const values = [...product.history, product.forecast / 7];
  const maxValue = Math.max(...values) * 1.12;
  const x = (index: number) => pad + index * ((width - pad * 2) / (values.length - 1));
  const y = (value: number) => height - pad - (value / maxValue) * (height - pad * 2);
  const historyPoints = product.history.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const forecastX = x(values.length - 1);
  const forecastY = y(product.forecast / 7);

  return (
    <div className="chart-wrap">
      <svg className="demand-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Fourteen-day demand history for ${product.id}`}>
        {[0.25, 0.5, 0.75].map((line) => <line key={line} x1={pad} x2={width-pad} y1={height*line} y2={height*line} className="grid-line" />)}
        <polyline points={historyPoints} className="history-line" />
        <line x1={x(product.history.length - 1)} y1={y(product.history.at(-1) ?? 0)} x2={forecastX} y2={forecastY} className="forecast-line" />
        <circle cx={forecastX} cy={forecastY} r="6" className="forecast-dot" />
      </svg>
      <div className="chart-axis"><span>14 days ago</span><span>Today</span><span>7-day forecast avg.</span></div>
    </div>
  );
}

export function InventoryDashboard() {
  const [products, setProducts] = useState(initialProducts);
  const [selectedId, setSelectedId] = useState(initialProducts[0].id);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"All" | "High" | "Reorder">("All");
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState("");
  const selected = products.find((product) => product.id === selectedId) ?? products[0];
  const visibleProducts = useMemo(() => products.filter((product) => {
    const matchesSearch = `${product.id} ${product.category} ${product.store}`.toLowerCase().includes(query.toLowerCase());
    const matchesFilter = filter === "All" || (filter === "High" && product.risk === "High") || (filter === "Reorder" && product.reorder > 0);
    return matchesSearch && matchesFilter;
  }), [filter, products, query]);
  const atRisk = products.filter((product) => product.risk === "High").length;
  const reorderCount = products.filter((product) => product.reorder > 0).length;

  async function refreshForecast() {
    setRefreshing(true);
    setMessage("");
    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product: selected.id,
          currentStock: selected.currentStock,
          safetyStock: selected.safetyStock,
          features: selected.features,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Forecast refresh failed.");
      const forecast = result as ApiResult;
      setProducts((current) => current.map((product) => product.id === selected.id ? {
        ...product,
        forecast: forecast.predictedDemand7Days,
        reorder: forecast.recommendedReorder,
        risk: riskLabel[forecast.riskLevel],
      } : product));
      setMessage("Forecast refreshed from the live DNN.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Forecast refresh failed.");
    } finally {
      setRefreshing(false);
    }
  }

  const coverage = Math.round((selected.currentStock / selected.forecast) * 100);

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="SmartStock dashboard home"><span className="brand-mark">S</span><span>SmartStock <b>AI</b></span></a>
        <div className="topbar-meta"><span className="model-status"><i />Model online</span><span className="separator"/><span>7-day horizon</span><span className="avatar">SA</span></div>
      </header>

      <div className="page-shell" id="top">
        <section className="page-heading">
          <div><p className="eyebrow">Inventory intelligence</p><h1>Demand &amp; reorder dashboard</h1><p>See what needs attention before it becomes a stockout.</p></div>
          <div className="as-of"><span>Forecast origin</span><strong>15 May 2016</strong><small>Final DNN · all stores</small></div>
        </section>

        <section className="metric-grid" aria-label="Key inventory metrics">
          <MetricCard label="Products at risk" value={String(atRisk)} note="Require immediate attention" icon="alert" tone="accent" />
          <MetricCard label="Average forecast error" value="3.37" note="MAE · final test set" icon="chart" />
          <MetricCard label="Products requiring reorder" value={String(reorderCount)} note={`Across ${products.length} monitored items`} icon="box" />
          <MetricCard label="Model WAPE" value="33.64%" note="14.29% better than naive" icon="target" />
        </section>

        <section className="panel inventory-panel">
          <div className="panel-heading">
            <div><p className="section-kicker">Priority queue</p><h2>Inventory decisions</h2><p>Forecast-led actions sorted by stock risk.</p></div>
            <div className="table-tools">
              <label className="search-box"><Icon name="search"/><span className="sr-only">Search products</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search product or store" /></label>
              <select value={filter} onChange={(event) => setFilter(event.target.value as typeof filter)} aria-label="Filter products">
                <option>All</option><option>High</option><option>Reorder</option>
              </select>
            </div>
          </div>
          <div className="table-scroll">
            <table>
              <thead><tr><th>Product</th><th>Store</th><th>Current stock</th><th>AI demand <span>7d</span></th><th>Reorder</th><th>Risk</th><th aria-label="Open detail"/></tr></thead>
              <tbody>
                {visibleProducts.map((product) => (
                  <tr key={`${product.store}-${product.id}`} className={selected.id === product.id ? "selected-row" : ""} onClick={() => setSelectedId(product.id)}>
                    <td><button className="product-button" onClick={() => setSelectedId(product.id)}><span className="product-cube">{product.category.slice(0, 1)}</span><span><strong>{product.id}</strong><small>{product.category}</small></span></button></td>
                    <td>{product.store}</td><td>{product.currentStock.toLocaleString()}</td><td><strong>{product.forecast.toLocaleString()}</strong></td><td className={product.reorder > 0 ? "reorder-value" : ""}>{product.reorder.toLocaleString()}</td><td><RiskBadge risk={product.risk}/></td><td className="row-arrow">→</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {visibleProducts.length === 0 && <div className="empty-state">No products match this filter.</div>}
          </div>
          <footer className="panel-foot"><span>Showing {visibleProducts.length} of {products.length} products</span><span>Inventory quantities are demonstration inputs.</span></footer>
        </section>

        <section className="panel detail-panel">
          <div className="panel-heading detail-heading">
            <div><p className="section-kicker">Product detail</p><h2>{selected.id}</h2><p>{selected.category} · {selected.store}</p></div>
            <div className="detail-actions"><RiskBadge risk={selected.risk}/><button className="refresh-button" onClick={refreshForecast} disabled={refreshing}>{refreshing ? "Refreshing…" : "Refresh with live model"}</button></div>
          </div>
          {message && <p className={`api-message ${message.includes("refreshed") ? "success" : "error"}`}>{message}</p>}
          <div className="detail-grid">
            <div className="history-card"><div className="chart-title"><div><h3>Historical demand</h3><p>Daily units · last 14 days</p></div><span className="legend-key"><i/>Observed demand</span></div><DemandChart product={selected}/></div>
            <aside className="recommendation-card">
              <p className="section-kicker">AI recommendation</p>
              <div className="forecast-number"><strong>{selected.forecast.toLocaleString()}</strong><span>units</span></div>
              <p>Predicted demand over the next 7 days</p>
              <div className="stock-meter"><div><span>Stock coverage</span><strong>{coverage}%</strong></div><div className="meter-track"><span style={{ width: `${Math.min(coverage, 100)}%` }}/></div></div>
              <dl><div><dt>Current inventory</dt><dd>{selected.currentStock.toLocaleString()}</dd></div><div><dt>Safety stock</dt><dd>{selected.safetyStock.toLocaleString()}</dd></div><div className="reorder-row"><dt>Recommended reorder</dt><dd>{selected.reorder.toLocaleString()} units</dd></div></dl>
              <p className="recommendation-note">{selected.reorder > 0 ? `Place an order for ${selected.reorder.toLocaleString()} units to cover forecast demand and restore the safety buffer.` : "Current inventory covers forecast demand and the safety buffer. No order is needed."}</p>
            </aside>
          </div>
        </section>
      </div>
    </main>
  );
}
