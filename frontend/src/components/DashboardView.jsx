import { useEffect, useState } from 'react';
import { Calendar, Tag, Clock, Activity } from 'lucide-react';

export default function DashboardView({ settings }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const colorMap = settings?.color_map || {};

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.json())
      .then(data => setStats(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="view-placeholder">
      <div className="loader-spinner" />
    </div>
  );

  if (!stats) return (
    <div className="view-placeholder">
      <p>No statistics available. Please check your settings.</p>
    </div>
  );

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <h2 className="dashboard__title">Recap Activity</h2>
        <p className="dashboard__subtitle">Overview of your scheduled events and categories</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card__icon stat-card__icon--blue">
            <Calendar size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">Total Events</span>
            <span className="stat-card__value">{stats.total_events}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card__icon stat-card__icon--green">
            <Tag size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">Categories</span>
            <span className="stat-card__value">{Object.keys(stats.categories).length}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card__icon stat-card__icon--amber">
            <Activity size={24} />
          </div>
          <div className="stat-card__info">
            <span className="stat-card__label">System Status</span>
            <span className="stat-card__value">Healthy</span>
          </div>
        </div>
      </div>

      <div className="dashboard__main">
        <div className="category-section">
          <h3 className="section-title">Category Breakdown</h3>
          <div className="category-list">
            {Object.entries(stats.categories).map(([cat, count]) => (
              <div key={cat} className="category-item">
                <div className="category-item__header">
                  <span className="category-item__name">{cat}</span>
                  <span className="category-item__count">{count}</span>
                </div>
                <div className="category-item__bar-wrap">
                  <div 
                    className="category-item__bar" 
                    style={{ 
                      width: `${(count / stats.total_events) * 100}%`,
                      backgroundColor: colorMap[cat] || '#3b82f6'
                    }} 
                  />
                </div>
              </div>
            ))}
            {Object.keys(stats.categories).length === 0 && (
              <p className="empty-msg">No categories found.</p>
            )}
          </div>
        </div>

        <div className="next-event-section">
          <h3 className="section-title">Coming Up Next</h3>
          <div className="next-event-card">
            {stats.next_event ? (
              <>
                <div className="next-event-card__header">
                  <span className="next-event-card__title">{stats.next_event.title}</span>
                  <span className="next-event-card__date">
                    {new Date(stats.next_event.start_date).toLocaleDateString(undefined, { 
                      month: 'long', day: 'numeric', year: 'numeric' 
                    })}
                  </span>
                </div>
                <div className="countdown">
                  <Countdown date={stats.next_event.start_date} />
                </div>
              </>
            ) : (
              <div className="empty-state">
                <Clock size={32} />
                <p>No upcoming events scheduled</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Countdown({ date }) {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    const target = new Date(date).getTime();
    
    const update = () => {
      const now = new Date().getTime();
      const diff = target - now;
      
      if (diff <= 0) {
        setTimeLeft('Happening today!');
        return;
      }
      
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      
      setTimeLeft(`${days}d ${hours}h ${mins}m`);
    };

    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [date]);

  return <span className="countdown__value">{timeLeft}</span>;
}
