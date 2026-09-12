export type Risk = "High" | "Watch" | "Healthy";

export type ForecastFeatures = Record<string, string | number>;

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
  features: ForecastFeatures;
};

const calendarFeatures = {
  days_since_release: 1933,
  day_of_week: 6,
  month: 5,
  is_weekend: 1,
  is_event: 0,
  dow_sin: -0.781832,
  dow_cos: 0.62349,
  month_sin: 0.5,
  month_cos: -0.866025,
};

export const initialProducts: Product[] = [
  {
    id: "FOODS_3_090",
    category: "Foods",
    store: "CA_1",
    currentStock: 220,
    safetyStock: 58,
    forecast: 391,
    reorder: 229,
    risk: "High",
    history: [59, 35, 47, 73, 89, 104, 77, 72, 46, 30, 35, 77, 47, 74],
    features: {
      lag_1: 47, lag_7: 77, lag_14: 71, lag_28: 83,
      rolling_mean_7: 54.857143, rolling_mean_14: 61.57143,
      rolling_mean_28: 59.714287, rolling_std_7: 20.111593,
      rolling_std_28: 23.124233, sales_sum_7: 384, sales_sum_28: 1672,
      zero_rate_28: 0, sell_price: 1.6, price_change: 0, price_change_pct: 0,
      ...calendarFeatures, dept_id: "FOODS_3", cat_id: "FOODS",
      store_id: "CA_1", state_id: "CA",
    },
  },
  {
    id: "HOUSEHOLD_1_191",
    category: "Household",
    store: "CA_2",
    currentStock: 100,
    safetyStock: 15,
    forecast: 84,
    reorder: 0,
    risk: "Healthy",
    history: [12, 12, 2, 0, 11, 21, 15, 7, 8, 9, 11, 11, 21, 24],
    features: {
      lag_1: 21, lag_7: 15, lag_14: 16, lag_28: 16,
      rolling_mean_7: 11.714286, rolling_mean_14: 11.142858,
      rolling_mean_28: 11.928572, rolling_std_7: 4.855042,
      rolling_std_28: 5.630134, sales_sum_7: 82, sales_sum_28: 334,
      zero_rate_28: 0.035714, sell_price: 2.96, price_change: 0,
      price_change_pct: 0, ...calendarFeatures, dept_id: "HOUSEHOLD_1",
      cat_id: "HOUSEHOLD", store_id: "CA_2", state_id: "CA",
    },
  },
  {
    id: "HOBBIES_1_234",
    category: "Hobbies",
    store: "TX_1",
    currentStock: 12,
    safetyStock: 6,
    forecast: 28,
    reorder: 22,
    risk: "High",
    history: [0, 1, 12, 3, 0, 2, 0, 0, 14, 0, 6, 4, 0, 4],
    features: {
      lag_1: 0, lag_7: 0, lag_14: 6, lag_28: 14,
      rolling_mean_7: 3.428571, rolling_mean_14: 3.428571,
      rolling_mean_28: 4.428571, rolling_std_7: 5.255383,
      rolling_std_28: 5.871643, sales_sum_7: 24, sales_sum_28: 124,
      zero_rate_28: 0.464286, sell_price: 0.3, price_change: 0,
      price_change_pct: 0, ...calendarFeatures, days_since_release: 1674,
      dept_id: "HOBBIES_1", cat_id: "HOBBIES", store_id: "TX_1",
      state_id: "TX",
    },
  },
  {
    id: "FOODS_3_586",
    category: "Foods",
    store: "TX_2",
    currentStock: 510,
    safetyStock: 70,
    forecast: 545,
    reorder: 105,
    risk: "High",
    history: [36, 60, 72, 92, 84, 117, 96, 72, 62, 69, 87, 85, 83, 103],
    features: {
      lag_1: 83, lag_7: 96, lag_14: 96, lag_28: 102,
      rolling_mean_7: 79.14286, rolling_mean_14: 79.35714,
      rolling_mean_28: 78.428574, rolling_std_7: 11.852265,
      rolling_std_28: 18.966694, sales_sum_7: 554, sales_sum_28: 2196,
      zero_rate_28: 0, sell_price: 1.68, price_change: 0, price_change_pct: 0,
      ...calendarFeatures, dept_id: "FOODS_3", cat_id: "FOODS",
      store_id: "TX_2", state_id: "TX",
    },
  },
  {
    id: "HOUSEHOLD_1_399",
    category: "Household",
    store: "WI_1",
    currentStock: 72,
    safetyStock: 12,
    forecast: 65,
    reorder: 5,
    risk: "Watch",
    history: [16, 9, 8, 12, 15, 17, 12, 8, 5, 21, 10, 13, 7, 9],
    features: {
      lag_1: 7, lag_7: 12, lag_14: 11, lag_28: 6,
      rolling_mean_7: 10.857142, rolling_mean_14: 11.714286,
      rolling_mean_28: 10.285714, rolling_std_7: 5.273474,
      rolling_std_28: 4.035556, sales_sum_7: 76, sales_sum_28: 288,
      zero_rate_28: 0, sell_price: 0.97, price_change: 0,
      price_change_pct: 0, ...calendarFeatures, days_since_release: 1751,
      dept_id: "HOUSEHOLD_1", cat_id: "HOUSEHOLD", store_id: "WI_1",
      state_id: "WI",
    },
  },
  {
    id: "HOBBIES_1_048",
    category: "Hobbies",
    store: "WI_3",
    currentStock: 55,
    safetyStock: 8,
    forecast: 40,
    reorder: 0,
    risk: "Healthy",
    history: [3, 9, 2, 6, 13, 18, 2, 2, 2, 2, 14, 3, 15, 17],
    features: {
      lag_1: 15, lag_7: 2, lag_14: 14, lag_28: 1,
      rolling_mean_7: 5.714286, rolling_mean_14: 7.5,
      rolling_mean_28: 6.178571, rolling_std_7: 6.019809,
      rolling_std_28: 5.497835, sales_sum_7: 40, sales_sum_28: 173,
      zero_rate_28: 0.071429, sell_price: 0.48, price_change: 0,
      price_change_pct: 0, ...calendarFeatures, days_since_release: 1926,
      dept_id: "HOBBIES_1", cat_id: "HOBBIES", store_id: "WI_3",
      state_id: "WI",
    },
  },
];
