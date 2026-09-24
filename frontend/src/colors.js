// Chart colors — validated categorical/sequential palette (dark mode steps),
// per the dataviz skill: fixed hue order, colorblind-safe on adjacent pairs.
// Reused as-is rather than re-derived for our exact surface (#16161f, close
// to the palette's own validated dark surface #1a1a19).

export const CATEGORICAL = {
  blue: "#3987e5",
  orange: "#d95926",
  aqua: "#199e70",
  yellow: "#c98500",
  magenta: "#d55181",
  green: "#008300",
  violet: "#9085e9",
  red: "#e66767",
};

// Fixed category -> color mapping so color always follows the entity, never
// its sorted rank (a category's color never changes if amounts shift).
export const SPENDING_CATEGORY_COLORS = {
  Shopping: CATEGORICAL.blue,
  Dining: CATEGORICAL.orange,
  Groceries: CATEGORICAL.aqua,
  Utilities: CATEGORICAL.yellow,
  Transport: CATEGORICAL.violet,
  Entertainment: CATEGORICAL.magenta,
  Other: CATEGORICAL.red,
};

export const CASHFLOW_COLORS = { in: CATEGORICAL.blue, out: CATEGORICAL.orange };
export const AMORTIZATION_COLORS = { principal: CATEGORICAL.blue, interest: CATEGORICAL.yellow };
export const SEQUENTIAL_BLUE = "#3987e5";

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const CHART_SURFACE = "#16161f";
export const TEXT_PRIMARY = "#ffffff";
export const TEXT_SECONDARY = "#c3c2b7";
export const TEXT_MUTED = "#898781";
export const GRIDLINE = "#2c2c2a";
