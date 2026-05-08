import { X, Calendar as CalendarIcon, MapPin, Tag, CheckCircle } from 'lucide-react';

export default function DayDetailsModal({ 
  day, tagsConfig, onClose, colorMap 
}) {
  if (!day) return null;
  const { date, events = [], advanced, special_tags: specialTags, where: locations } = day;
  
  // Use unified metadata if available, or fallback to day fields
  const fiscalMonth = day.fiscal_month || advanced?.fiscal_month;
  const fiscalWeek = day.week_of_month || advanced?.fiscal_week;
  const season = day.season || advanced?.season;

  const formattedDate = new Date(date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--day-details" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div className="modal__title">
            <CalendarIcon size={20} />
            <div>
              <h2>{formattedDate}</h2>
            </div>
          </div>
          <button className="modal__close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal__body">
          {/* Metadata Section */}
          {((specialTags?.length > 0) || (day?.tier3?.cultural && day.tier3.cultural.length > 0)) && (
            <div className="advanced-metadata-panel">
              {/* Unified Cultural Data */}
              {day?.tier3?.cultural && day.tier3.cultural.length > 0 && (
                <div className="cultural-metadata" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {day.tier3.cultural.map((c, i) => (
                    <div key={i} style={{ 
                      fontSize: '0.7rem', 
                      padding: '4px 8px', 
                      borderRadius: '12px', 
                      backgroundColor: '#f0f4f8',
                      color: '#4a5568',
                      border: '1px solid #e2e8f0',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      {c.type === 'holiday' ? '🎉' : '🌍'} {c.name} {c.country ? `(${c.country})` : ''}
                    </div>
                  ))}
                </div>
              )}

              {specialTags?.length > 0 && tagsConfig && (
                <div className="tags-row" style={{ marginTop: day?.tier3?.cultural?.length > 0 ? '12px' : '0' }}>
                  {specialTags.map(tagId => {
                    const tag = tagsConfig.primary.find(t => t.id === tagId);
                    if (!tag) return null;
                    return (
                      <span key={tagId} className="meta-tag" style={{ backgroundColor: tag.color + '20', color: tag.color, borderColor: tag.color }}>
                        {tag.label}
                      </span>
                    );
                  })}
                  {locations?.map(locId => {
                    const loc = tagsConfig.where.find(t => t.id === locId);
                    if (!loc) return null;
                    return (
                      <span key={locId} className="meta-tag meta-tag--loc">
                        <MapPin size={10} /> {loc.label}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          <div className="section-divider" />
          {events.length === 0 ? (
            <div className="empty-state">
              <p>No events scheduled for this day.</p>
            </div>
          ) : (
            <div className="day-event-list">
              {events.map((ev, i) => {
                const color = colorMap?.[ev.category] || '#3b82f6';
                return (
                  <div className="day-event-card" key={i} style={{ '--event-color': color }}>
                    <div className="day-event-card__side" />
                    <div className="day-event-card__content">
                      <div className="day-event-card__header">
                        <h3 className="day-event-card__title">{ev.title}</h3>
                        <span className="day-event-card__category" style={{ backgroundColor: `${color}20`, color: color }}>
                          {ev.category}
                        </span>
                      </div>
                      
                      <div className="day-event-card__details">
                        <div className="detail-item">
                          <Tag size={14} />
                          <span>{ev.type || 'Event'}</span>
                        </div>
                        {ev.place && (
                          <div className="detail-item">
                            <MapPin size={14} />
                            <span>{ev.place}</span>
                          </div>
                        )}
                        <div className="detail-item">
                          <CheckCircle size={14} />
                          <span>{ev.status || 'Confirmed'}</span>
                        </div>
                      </div>

                      <div className="day-event-card__time">
                        {ev.start_date === ev.end_date ? (
                          <span>All Day</span>
                        ) : (
                          <span>From {ev.start_date} to {ev.end_date}</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
