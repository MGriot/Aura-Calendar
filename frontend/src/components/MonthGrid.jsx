const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

export default function MonthGrid({ month, today, allEvents = [], settings, tagsConfig, onDayClick }) {
  const colorMap = settings?.color_map || {};

  return (
    <section className="month-card" id={`month-${month.year}-${month.month}`}>
      <div className="month-card__header">
        <span className="month-card__name">{month.month_name}</span>
        <span className="month-card__year">{month.year}</span>
      </div>

      {/* Weekday header row */}
      <div className="week-row week-row--header">
        <div className="cw-cell cw-cell--header">CW</div>
        <div className="week-grid">
          {WEEKDAYS.map((d, i) => (
            <div
              key={d}
              className={`weekday-cell${i >= 5 ? ' weekday-cell--weekend' : ''}`}
              style={{ textAlign: 'center', padding: '8px 0', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)' }}
            >
              {d}
            </div>
          ))}
        </div>
      </div>

      {/* Week rows */}
      {month.weeks.map((week, wi) => {
        const weekStart = week.days[0].date;
        const weekEnd = week.days[6].date;

        // 1. Find events intersecting this week
        const weekEvents = allEvents.filter(ev => 
          ev.start_date <= weekEnd && ev.end_date >= weekStart
        );

        // 2. Assign tracks (greedy layout)
        const tracks = [];
        weekEvents.forEach(ev => {
          let trackIdx = tracks.findIndex(track => 
            track.every(existing => 
              ev.start_date > existing.end_date || ev.end_date < existing.start_date
            )
          );
          if (trackIdx === -1) {
            tracks.push([ev]);
          } else {
            tracks[trackIdx].push(ev);
          }
        });

        return (
          <div className="week-row" key={wi}>
            <div className="cw-cell">{week.cw}</div>
            
            {/* Day Cells Layer */}
            <div className="week-grid">
              {week.days.map((day) => {
                const isToday = day.date === today;
                const isWeekend = day.day_of_week >= 5;
                const hasSpecial = day.special;
                
                const cls = [
                  'day-cell',
                  !day.is_current_month && 'day-cell--outside',
                  isToday && 'day-cell--today',
                  isWeekend && 'day-cell--weekend',
                  hasSpecial && 'day-cell--special',
                ].filter(Boolean).join(' ');

                let style = {};
                if (hasSpecial && tagsConfig) {
                  const primaryTag = tagsConfig.primary.find(t => day.special.tags.includes(t.id));
                  if (primaryTag) {
                    style.backgroundColor = primaryTag.color + '22'; // 13% opacity
                    style.borderBottom = `3px solid ${primaryTag.color}`;
                  }
                }

                return (
                  <div className={cls} key={day.date} onClick={() => onDayClick(day)} style={style}>
                    <span className="day-cell__number">{day.day}</span>
                  </div>
                );
              })}
            </div>

            {/* Banners Layer */}
            <div className="banners-layer" style={{ left: '40px' }}>
              {tracks.map((track, trackIdx) => (
                <div key={trackIdx} style={{ position: 'relative', height: '26px' }}>
                  {track.map((ev, i) => {
                    const sIdx = week.days.findIndex(d => d.date === ev.start_date);
                    const eIdx = week.days.findIndex(d => d.date === ev.end_date);
                    
                    const spanStart = sIdx === -1 ? 0 : sIdx;
                    const spanEnd = eIdx === -1 ? 6 : eIdx;
                    
                    const color = colorMap[ev.category] || '#3b82f6';
                    
                    return (
                      <div 
                        key={i}
                        className="event-banner"
                        style={{
                          gridColumn: `${spanStart + 1} / ${spanEnd + 2}`,
                          position: 'absolute',
                          left: `${(spanStart / 7) * 100}%`,
                          width: `${((spanEnd - spanStart + 1) / 7) * 100}%`,
                          '--banner-color': color,
                          borderRadius: `${sIdx === -1 ? '0' : '4px'} ${eIdx === -1 ? '0' : '4px'} ${eIdx === -1 ? '0' : '4px'} ${sIdx === -1 ? '0' : '4px'}`
                        }}
                        title={`${ev.title} (${ev.category})`}
                      >
                        {(sIdx !== -1 || spanStart === 0) && (
                          <span className="event-banner__title">{ev.title}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}
