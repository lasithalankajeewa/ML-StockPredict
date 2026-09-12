import "server-only";

import { readFileSync } from "node:fs";
import path from "node:path";

import type {
  CatalogSummary,
  Product,
  ProductFilters,
  ProductPage,
} from "@/lib/dashboard-data";

let cachedProducts: Product[] | undefined;
let cachedSummary: CatalogSummary | undefined;
let cachedStores: string[] | undefined;

function getProducts() {
  if (!cachedProducts) {
    const catalogPath = path.join(process.cwd(), "data", "products.json");
    cachedProducts = JSON.parse(readFileSync(catalogPath, "utf8")) as Product[];
  }
  return cachedProducts;
}

function getSummary(products: Product[]) {
  if (!cachedSummary) {
    cachedSummary = {
      totalProducts: products.length,
      productsAtRisk: products.filter((product) => product.risk === "High").length,
      productsRequiringReorder: products.filter((product) => product.reorder > 0).length,
    };
  }
  return cachedSummary;
}

function getStores(products: Product[]) {
  if (!cachedStores) {
    cachedStores = [...new Set(products.map((product) => product.store))].sort();
  }
  return cachedStores;
}

export function queryProducts(filters: ProductFilters = {}): ProductPage {
  const products = getProducts();
  const search = filters.search?.trim().toLowerCase() ?? "";
  const store = filters.store?.trim() ?? "All";
  const risk = filters.risk ?? "All";
  const pageSize = Math.min(Math.max(filters.pageSize ?? 25, 1), 100);

  const filtered = products.filter((product) => {
    const matchesSearch =
      !search ||
      product.id.toLowerCase().includes(search) ||
      product.category.toLowerCase().includes(search) ||
      product.store.toLowerCase().includes(search);
    const matchesStore = store === "All" || product.store === store;
    const matchesRisk =
      risk === "All" ||
      (risk === "High" && product.risk === "High") ||
      (risk === "Reorder" && product.reorder > 0);
    return matchesSearch && matchesStore && matchesRisk;
  });

  filtered.sort((left, right) => {
    const riskOrder = { High: 0, Watch: 1, Healthy: 2 };
    return (
      riskOrder[left.risk] - riskOrder[right.risk] ||
      right.reorder - left.reorder ||
      left.id.localeCompare(right.id) ||
      left.store.localeCompare(right.store)
    );
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const page = Math.min(Math.max(filters.page ?? 1, 1), totalPages);
  const start = (page - 1) * pageSize;

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
    totalPages,
    summary: getSummary(products),
    stores: getStores(products),
  };
}
