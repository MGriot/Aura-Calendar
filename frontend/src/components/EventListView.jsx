import { useEffect, useState } from 'react';
import { Search, Filter, Calendar as CalIcon } from 'lucide-react';

export default function EventListView({ allEvents = [], settings }) {
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('all');
  const [filtered, setFiltered] = useState(allEvents);

  const colorMap = settings?.color_map || {};

  useEffect(() => {
    let res = allEvents;
    if (search) {
      res = res.filter(ev => 
        ev.title.toLowerCase().includes(search.toLowerCase()) ||
        ev.category.toLowerCase().includes(search.toLowerCase())
      );
    }
    if (catFilter !== 'all') {
      res = res.filter(ev => ev.category === catFilter);
    }
    setFiltered(res);
  }, [search, catFilter, allEvents]);

  const categories = ['all', ...new Set(allEvents.map(ev => ev.category))];

  return (
    <div className="event-list-view">
      <div className="event-list-view__header">
        <h2 className="event-list-view__title">Nearest Events</h2>
        <div className="event-list-view__filters">
          <div className="search-box">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search events..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="filter-box">
            <Filter size={16} />
            <select value={catFilter} onChange={(e) => setCatFilter(e.target.value)}>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat === 'all' ? 'All Categories' : cat}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="event-list">
        {filtered.map((ev, i) => (
          <div key={i} className="event-list-item">
            <div className="event-list-item__date">
              <CalIcon size={18} />
              <span>{new Date(ev.start_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span>
            </div>
            <div className="event-list-item__info">
              <span className="event-list-item__title">{ev.title}</span>
              <span 
                className="event-list-item__category" 
                style={{ 
                  backgroundColor: `${colorMap[ev.category] || '#3b82f6'}20`, 
                  color: colorMap[ev.category] || '#3b82f6' 
                }}
              >
                {ev.category}
              </span>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="empty-state">
            <p>No events found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}
