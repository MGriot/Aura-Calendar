import { X, Calendar as CalendarIcon, MapPin, Tag, CheckCircle } from 'lucide-react';

export default function DayDetailsModal({ date, events, onClose, colorMap }) {
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
              <p className="modal__subtitle">{events.length} {events.length === 1 ? 'event' : 'events'} scheduled</p>
            </div>
          </div>
          <button className="modal__close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal__body">
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
