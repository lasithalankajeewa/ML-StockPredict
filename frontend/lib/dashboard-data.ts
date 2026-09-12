export type Risk = "High" | "Watch" | "Healthy";

export type Product = {
  id: string;
  category: string;
  store: string;
  currentStock: number;
  safetyStock: number;
  forecast: number;
  reorder: number;
  risk: Risk;
  history: number[];
};

export type CatalogSummary = {
  totalProducts: number;
  productsAtRisk: number;
  productsRequiringReorder: number;
};

export type ProductPage = {
  items: Product[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  summary: CatalogSummary;
  stores: string[];
};

export type ProductFilters = {
  search?: string;
  store?: string;
  risk?: "All" | "High" | "Reorder";
  page?: number;
  pageSize?: number;
};
