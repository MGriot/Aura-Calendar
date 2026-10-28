export const DEFAULT_EVENT_COLOR = '#3b82f6';

export function getCategoryColor(settings, category) {
  return settings?.color_map?.[category] || DEFAULT_EVENT_COLOR;
}
