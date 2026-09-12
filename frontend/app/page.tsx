import { InventoryDashboard } from "@/components/inventory-dashboard";
import type { ProductFilters } from "@/lib/dashboard-data";
import { queryProducts } from "@/lib/product-catalog";

type HomeProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;
  const requestedRisk = firstValue(params.risk);
  const risk: ProductFilters["risk"] =
    requestedRisk === "High" || requestedRisk === "Reorder" ? requestedRisk : "All";
  const filters: ProductFilters = {
    search: firstValue(params.search),
    store: firstValue(params.store) || "All",
    risk,
  };

  return <InventoryDashboard initialData={queryProducts(filters)} initialFilters={filters} />;
}
