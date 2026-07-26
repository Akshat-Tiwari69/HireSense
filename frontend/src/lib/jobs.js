const INDIA_UTC_OFFSET_MS = 5.5 * 60 * 60 * 1000;

export const toJobClosingInputValue = (value) => {
  if (!value) return '';
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return '';
  return new Date(timestamp + INDIA_UTC_OFFSET_MS).toISOString().slice(0, 16);
};
