const CATEGORY_COLORS = {
  holiday: 'var(--accent-red)',
  sprint: 'var(--accent-blue)',
  review: 'var(--accent-green)',
  meeting: 'var(--accent-purple)',
  deadline: 'var(--accent-amber)',
  default: 'var(--accent-cyan)',
};

const FALLBACK_PALETTE = [
  'var(--accent-blue)',
  'var(--accent-green)',
  'var(--accent-amber)',
  'var(--accent-purple)',
  'var(--accent-cyan)',
  'var(--accent-pink)',
  'var(--accent-red)',
];

function getCategoryColor(category) {
  if (!category) return CATEGORY_COLORS.default;
  const lower = category.toLowerCase();
  if (CATEGORY_COLORS[lower]) return CATEGORY_COLORS[lower];
  // Hash-based fallback for unknown categories
  let hash = 0;
  for (let i = 0; i < lower.length; i++) {
    hash = lower.charCodeAt(i) + ((hash << 5) - hash);
  }
  return FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
}

export default function EventBadge({ event }) {
  const color = getCategoryColor(event.category);

  return (
    <span
      className="event-badge"
      style={{
        '--badge-color': color,
      }}
      title={`${event.title} (${event.category})`}
    >
      {event.title}
    </span>
  );
}
