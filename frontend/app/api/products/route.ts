import { NextRequest, NextResponse } from "next/server";

import type { ProductFilters } from "@/lib/dashboard-data";
import { queryProducts } from "@/lib/product-catalog";

function positiveInteger(value: string | null, fallback: number) {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const requestedRisk = params.get("risk");
  const risk: ProductFilters["risk"] =
    requestedRisk === "High" || requestedRisk === "Reorder" ? requestedRisk : "All";

  return NextResponse.json(
    queryProducts({
      search: params.get("search") ?? "",
      store: params.get("store") ?? "All",
      risk,
      page: positiveInteger(params.get("page"), 1),
      pageSize: positiveInteger(params.get("pageSize"), 25),
    }),
  );
}
