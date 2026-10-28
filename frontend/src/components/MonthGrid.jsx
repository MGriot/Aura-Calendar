import { useMemo } from 'react';
import { getCategoryColor } from '../utils/colors.js';

const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

// Greedy track assignment: longest events first among those starting the same day,
// so multi-day banners stay on top and single-day events pack below them.
function assignTracks(events) {
  const sorted = [...events].sort((a, b) =>
    a.start_date.localeCompare(b.start_date) || b.end_date.localeCompare(a.end_date)
  );
  const trackEnds = []; // last end_date per track
  return sorted.map(ev => {
    let track = trackEnds.findIndex(end => end < ev.start_date);
    if (track === -1) {
      track = trackEnds.length;
      trackEnds.push(ev.end_date);
    } else {
      trackEnds[track] = ev.end_date;
    }
    return { ev, track };
  });
}

export default function MonthGrid({ month, today, allEvents = [], settings, tagsConfig, onDayClick }) {
  const showSpecial = settings?.show_special_days ?? true;

  const weekLayouts = useMemo(() => month.weeks.map(week => {
    const weekStart = week.days[0].date;
    const weekEnd = week.days[6].date;
    const placed = assignTracks(
      allEvents.filter(ev => ev.start_date <= weekEnd && ev.end_date >= weekStart)
    );
    return placed.map(({ ev, track }) => {
      const sIdx = week.days.findIndex(d => d.date === ev.start_date);
      const eIdx = week.days.findIndex(d => d.date === ev.end_date);
      return {
        ev,
        track,
        start: ev.start_date < weekStart ? 0 : sIdx,
        end: ev.end_date > weekEnd ? 6 : eIdx,
        contLeft: ev.start_date < weekStart,
        contRight: ev.end_date > weekEnd,
      };
    });
  }), [month, allEvents]);

  return (
    <section className="month-card" id={`month-${month.year}-${month.month}`}>
      <div className="month-card__header">
        <span className="month-card__name">{month.month_name}</span>
        <span className="month-card__year">{month.year}</span>
      </div>

      {/* Weekday header row */}
      <div className="week-row week-row--header">
        <div className="cw-cell cw-cell--header">CW</div>
        {WEEKDAYS.map((d, i) => (
          <div key={d} className={`weekday-cell${i >= 5 ? ' weekday-cell--weekend' : ''}`}>{d}</div>
        ))}
      </div>

      {/* Week rows */}
      {month.weeks.map((week, wi) => {
        const trackCount = weekLayouts[wi].reduce((n, b) => Math.max(n, b.track + 1), 0);
        const rowStyle = trackCount > 0
          ? { gridTemplateRows: `auto repeat(${trackCount}, var(--banner-h))` }
          : undefined;
        return (
        <div className="week-row" key={wi} style={rowStyle}>
          <div className="cw-cell">{week.cw}</div>

          {/* Background / click layer: one cell per day spanning all rows */}
          {week.days.map((day, di) => {
            const hasSpecial = showSpecial && day.special_tags?.length > 0;
            const primaryTag = hasSpecial && tagsConfig
              ? tagsConfig.primary.find(t => day.special_tags.includes(t.id))
              : null;
            const mainHol = day.tier3?.cultural?.[0];

            const style = { gridColumn: di + 2 };
            if (primaryTag) {
              style.backgroundColor = primaryTag.color + '22'; // 13% opacity
              style.boxShadow = `inset 0 -3px 0 ${primaryTag.color}`;
            } else if (mainHol) {
              style.backgroundColor = mainHol.color + '40'; // 25% opacity
            }
            if (mainHol) style.borderLeft = `4px solid ${mainHol.color}`;

            const cls = [
              'day-cell',
              !day.is_current_month && 'day-cell--outside',
              day.date === today && 'day-cell--today',
              day.day_of_week >= 5 && 'day-cell--weekend',
            ].filter(Boolean).join(' ');

            return <div className={cls} key={day.date} style={style} onClick={() => onDayClick(day)} />;
          })}

          {/* Day heads: number, special tag and cultural labels (row 1) */}
          {week.days.map((day, di) => {
            const hasSpecial = showSpecial && day.special_tags?.length > 0;
            const primaryTag = hasSpecial && tagsConfig
              ? tagsConfig.primary.find(t => day.special_tags.includes(t.id))
              : null;
            const cls = [
              'day-head',
              !day.is_current_month && 'day-head--outside',
              day.date === today && 'day-head--today',
            ].filter(Boolean).join(' ');

            return (
              <div className={cls} key={`h-${day.date}`} style={{ gridColumn: di + 2 }}>
                <div className="day-head__top">
                  <span className="day-cell__number">{day.day}</span>
                  {primaryTag && (
                    <span className="day-head__tag" style={{ color: primaryTag.color }}>{primaryTag.label}</span>
                  )}
                </div>
                {day.tier3?.cultural?.length > 0 && (
                  <div className="day-head__cultural">
                    {day.tier3.cultural.map((c, i) => (
                      <div key={i} title={c.name} style={{ color: c.color }}>{c.name}</div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Event banners: one grid row per track, so rows grow instead of overlapping */}
          {weekLayouts[wi].map(({ ev, track, start, end, contLeft, contRight }, i) => (
            <div
              key={i}
              className={[
                'event-banner',
                contLeft && 'event-banner--cont-left',
                contRight && 'event-banner--cont-right',
              ].filter(Boolean).join(' ')}
              style={{
                gridColumn: `${start + 2} / ${end + 3}`,
                gridRow: track + 2,
                '--banner-color': getCategoryColor(settings, ev.category),
              }}
              title={`${ev.title} (${ev.category})`}
              onClick={() => onDayClick(week.days[start])}
            >
              <span className="event-banner__title">{ev.title}</span>
            </div>
          ))}
        </div>
        );
      })}
    </section>
  );
}
