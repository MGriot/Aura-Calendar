import { useEffect, useState } from 'react';

export default function WeekView({ onDayClick, startYear, startMonth, startDay, settings, tagsConfig }) {
  const [week, setWeek] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // Fetch the week containing the anchor day (defaults provided by App)
    const dayParam = typeof startDay !== 'undefined' ? startDay : 1;
    fetch(`/api/week?year=${startYear}&month=${startMonth}&day=${dayParam}`)
      .then(r => r.json())
      .then(data => setWeek(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startYear, startMonth, startDay]);

  if (loading) return (
    <div className="view-placeholder">
      <div className="loader-spinner" />
    </div>
  );

  if (!week) return (
    <div className="view-placeholder">
      <p>Could not load week data.</p>
    </div>
  );

  const showSpecial = settings?.show_special_days ?? true;

  return (
    <div className="week-view">
      <div className="week-view__header">
        <h2 className="week-view__title">Weekly Schedule</h2>
        <p className="week-view__subtitle">Current week overview</p>
      </div>

      <div className="week-timeline">
        {week.days.map((day) => {
          const hasAdvanced = !!day.advanced;
          const hasSpecial = showSpecial && day.special_tags?.length > 0;
          
          let dayStyle = { cursor: 'pointer' };
          let primaryTag = null;
          if (hasSpecial && tagsConfig) {
            primaryTag = tagsConfig.primary.find(t => day.special_tags?.includes(t.id));
            if (primaryTag) {
              dayStyle.backgroundColor = primaryTag.color + '10'; // very light background
              dayStyle.borderTop = `3px solid ${primaryTag.color}`;
            }
          }

          return (
            <div 
              key={day.date} 
              className={`week-day ${day.is_today ? 'week-day--today' : ''}`}
              onClick={() => onDayClick?.(day)}
              style={dayStyle}
            >
              <div className="week-day__header">
                <span className="week-day__name">{day.day_name.slice(0, 3)}</span>
                <span className="week-day__date">{day.day}</span>
                <span className="week-day__month">{day.month_name.slice(0, 3)}</span>
                
                {primaryTag && (
                  <span style={{
                    marginLeft: '8px',
                    fontSize: '0.65rem',
                    fontWeight: 800,
                    color: primaryTag.color,
                    textTransform: 'uppercase'
                  }}>
                    {primaryTag.label}
                  </span>
                )}
                
                {hasAdvanced && (
                  <div className="week-day__adv">
                    <span title="Fiscal Month">M{day.advanced.fiscal_month}</span>
                    <span title="Fiscal Week">W{day.advanced.fiscal_week}</span>
                  </div>
                )}
              </div>

              <div className="week-day__events">
                {day.tier1 && day.tier1.map((ev, i) => (
                  <div 
                    key={i} 
                    className="week-event"
                    style={{ borderLeftColor: `var(--accent-${ev.category === 'default' ? 'blue' : 'purple'})` }}
                  >
                    <span className="week-event__title">{ev.title}</span>
                    <span className="week-event__cat">{ev.category}</span>
                  </div>
                ))}
                {(!day.tier1 || day.tier1.length === 0) && (
                  <div className="week-event--empty">No events</div>
                )}
              </div>

              {/* Tier 3: Cultural info */}
              {day.tier3?.cultural && day.tier3.cultural.length > 0 && (
                <div className="week-day__cultural" style={{ padding: '4px 8px', borderTop: '1px dashed #eee' }}>
                  {day.tier3.cultural.map((c, i) => (
                    <div key={i} style={{ fontSize: '0.65rem', color: '#666', fontStyle: 'italic' }}>
                      {c.type === 'holiday' ? '🎉 ' : '🌙 '}{c.name}
                    </div>
                  ))}
                </div>
              )}

              {hasAdvanced && (
                <div className="week-day__footer">
                  <span className="season-tag">{day.advanced.season}</span>
                  {day.advanced.holidays && Object.keys(day.advanced.holidays).length > 0 && (
                    <span className="holiday-tag" title={Object.values(day.advanced.holidays).join(', ')}>
                      Holiday
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
