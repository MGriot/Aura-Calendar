import { useState, useEffect } from 'react';
import { Save, Trash2, Plus, Minus, Check, X } from 'lucide-react';

const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

export default function SpecialDaysView({ settings }) {
  const [yearData, setYearData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDates, setSelectedDates] = useState([]);
  const [tagsConfig, setTagsConfig] = useState(null);
  const [specialDays, setSpecialDays] = useState([]);
  const [viewYear, setViewYear] = useState(new Date().getFullYear());
  
  // Selection state
  const [formTags, setFormTags] = useState([]);
  const [formWhere, setFormWhere] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/calendar?start_month=1&start_year=${viewYear}&num_months=12`);
      const data = await res.json();
      setYearData(data.months);
      setTagsConfig(data.tags_config);
      setSpecialDays(data.special_days);
    } catch (err) {
      console.error("Failed to fetch year data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [viewYear]);

  const toggleDate = (date) => {
    setSelectedDates(prev => 
      prev.includes(date) ? prev.filter(d => d !== date) : [...prev, date]
    );
  };

  const handleAssign = async () => {
    if (selectedDates.length === 0) return;
    try {
      const res = await fetch('/api/special-days/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dates: selectedDates,
          tags: formTags,
          where: formWhere
        })
      });
      if (res.ok) {
        setSelectedDates([]);
        fetchData();
      }
    } catch (err) {
      console.error("Failed to assign tags:", err);
    }
  };

  const addTag = async (type) => {
    const labelInput = document.getElementById(`new-${type}-label`);
    const colorInput = document.getElementById(`new-${type}-color`);
    if (!labelInput.value) return;

    const newTag = {
      id: labelInput.value.toLowerCase().replace(/\s+/g, '_'),
      label: labelInput.value,
      color: colorInput.value
    };

    const newConfig = { ...tagsConfig };
    newConfig[type] = [...newConfig[type], newTag];

    try {
      const res = await fetch('/api/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      if (res.ok) {
        labelInput.value = "";
        fetchData();
      }
    } catch (err) {
      console.error("Failed to add tag:", err);
    }
  };

  const removeTag = async (type, id) => {
    const newConfig = { ...tagsConfig };
    newConfig[type] = newConfig[type].filter(t => t.id !== id);

    try {
      const res = await fetch('/api/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error("Failed to remove tag:", err);
    }
  };

  if (loading) return <div className="loader"><div className="loader-spinner" /></div>;

  return (
    <div className="special-days-view">
      <header className="special-days-view__header">
        <div className="header__left">
          <h2 className="special-days-view__title">Annual Tagging View</h2>
          <div className="year-nav">
            <button className="nav-btn" onClick={() => setViewYear(v => v - 1)}><Minus size={16} /></button>
            <span className="year-display">{viewYear}</span>
            <button className="nav-btn" onClick={() => setViewYear(v => v + 1)}><Plus size={16} /></button>
          </div>
        </div>
      </header>

      <div className="special-days-layout">
        <div className="year-grid">
          {yearData?.map((month) => (
            <div key={`${month.year}-${month.month}`} className="mini-month">
              <div className="mini-month__header">
                {month.month_name}
              </div>
              <div className="mini-month__days">
                {WEEKDAYS.map(d => <div key={d} className="mini-day-header">{d}</div>)}
                {month.weeks.map(week => week.days.map(day => {
                  const isSelected = selectedDates.includes(day.date);
                  const isSpecial = specialDays.find(sd => sd.date === day.date);
                  const isCurrentMonth = day.is_current_month;
                  
                  let style = {};
                  if (isSpecial && tagsConfig) {
                    const primaryTag = tagsConfig.primary.find(t => isSpecial.tags.includes(t.id));
                    if (primaryTag) {
                      style.backgroundColor = primaryTag.color + '33';
                      style.borderBottom = `2px solid ${primaryTag.color}`;
                    }
                  }

                  return (
                    <div 
                      key={day.date} 
                      className={`mini-day ${!isCurrentMonth ? 'mini-day--outside' : ''} ${isSelected ? 'mini-day--selected' : ''}`}
                      onClick={() => isCurrentMonth && toggleDate(day.date)}
                      style={style}
                    >
                      {day.day}
                    </div>
                  );
                }))}
              </div>
            </div>
          ))}
        </div>

        <div className="special-days-sidebar">
          <div className="sidebar-section">
            <h3 className="sidebar-title">Tag Assignment</h3>
            <p className="sidebar-subtitle">{selectedDates.length} days selected</p>
            
            <div className="form-section">
              <label>Primary Tags</label>
              <div className="tag-chips">
                {tagsConfig?.primary.map(tag => (
                  <button 
                    key={tag.id}
                    className={`tag-chip ${formTags.includes(tag.id) ? 'tag-chip--active' : ''}`}
                    onClick={() => setFormTags(prev => 
                      prev.includes(tag.id) ? prev.filter(t => t !== tag.id) : [...prev, tag.id]
                    )}
                    style={{ '--tag-color': tag.color }}
                  >
                    {tag.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-section">
              <label>Location (Where)</label>
              <select className="field__select" value={formWhere} onChange={(e) => setFormWhere(e.target.value)}>
                <option value="">None</option>
                {tagsConfig?.where.map(tag => (
                  <option key={tag.id} value={tag.id}>{tag.label}</option>
                ))}
              </select>
            </div>

            <button className="btn btn--primary" onClick={handleAssign} disabled={selectedDates.length === 0} style={{ width: '100%' }}>
              <Save size={16} /> Apply Tags
            </button>
          </div>

          <hr className="divider" />

          <div className="tag-management">
            <h3 className="sidebar-title">Manage Taxonomy</h3>
            
            <div className="form-section">
              <label>Primary Categories</label>
              <div className="tag-list-edit">
                {tagsConfig?.primary.map(tag => (
                  <div key={tag.id} className="tag-edit-item">
                    <div className="tag-edit-item__info">
                      <div className="tag-dot" style={{ backgroundColor: tag.color }} />
                      <span className="tag-label">{tag.label}</span>
                    </div>
                    <button className="icon-btn icon-btn--danger" onClick={() => removeTag('primary', tag.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                <div className="tag-add-row">
                  <div className="tag-add-inputs">
                    <input type="text" className="field__input" placeholder="New tag..." id="new-primary-label" />
                    <input type="color" className="color-picker-input" id="new-primary-color" defaultValue="#3b82f6" />
                  </div>
                  <button className="icon-btn icon-btn--primary" onClick={() => addTag('primary')}>
                    <Plus size={16} />
                  </button>
                </div>
              </div>
            </div>

            <div className="form-section">
              <label>Locations (Where)</label>
              <div className="tag-list-edit">
                {tagsConfig?.where.map(tag => (
                  <div key={tag.id} className="tag-edit-item">
                    <div className="tag-edit-item__info">
                      <div className="tag-dot" style={{ backgroundColor: tag.color }} />
                      <span className="tag-label">{tag.label}</span>
                    </div>
                    <button className="icon-btn icon-btn--danger" onClick={() => removeTag('where', tag.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                <div className="tag-add-row">
                  <div className="tag-add-inputs">
                    <input type="text" className="field__input" placeholder="New location..." id="new-where-label" />
                    <input type="color" className="color-picker-input" id="new-where-color" defaultValue="#64748b" />
                  </div>
                  <button className="icon-btn icon-btn--primary" onClick={() => addTag('where')}>
                    <Plus size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
