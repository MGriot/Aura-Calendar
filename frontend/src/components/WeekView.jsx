import { useEffect, useState } from 'react';

export default function WeekView() {
  const [week, setWeek] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/week')
      .then(r => r.json())
      .then(data => setWeek(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

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

  return (
    <div className="week-view">
      <div className="week-view__header">
        <h2 className="week-view__title">Weekly Schedule</h2>
        <p className="week-view__subtitle">Current week overview</p>
      </div>

      <div className="week-timeline">
        {week.days.map((day) => (
          <div 
            key={day.date} 
            className={`week-day ${day.is_today ? 'week-day--today' : ''}`}
          >
            <div className="week-day__header">
              <span className="week-day__name">{day.day_name.slice(0, 3)}</span>
              <span className="week-day__date">{day.day}</span>
              <span className="week-day__month">{day.month_name.slice(0, 3)}</span>
            </div>

            <div className="week-day__events">
              {day.events.map((ev, i) => (
                <div 
                  key={i} 
                  className="week-event"
                  style={{ borderLeftColor: `var(--accent-${ev.category === 'default' ? 'blue' : 'purple'})` }}
                >
                  <span className="week-event__title">{ev.title}</span>
                  <span className="week-event__cat">{ev.category}</span>
                </div>
              ))}
              {day.events.length === 0 && (
                <div className="week-event--empty">No events</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
