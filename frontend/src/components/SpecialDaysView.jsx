import { useState, useEffect } from 'react';
import { Save, Trash2, Plus, Check, X } from 'lucide-react';

const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

export default function SpecialDaysView({ settings }) {
  const [yearData, setYearData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDates, setSelectedDates] = useState([]);
  const [tagsConfig, setTagsConfig] = useState(null);
  const [specialDays, setSpecialDays] = useState([]);
  
  // Selection state
  const [formTags, setFormTags] = useState([]);
  const [formWhere, setFormWhere] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const currentYear = new Date().getFullYear();
      const res = await fetch(`/api/calendar?start_month=1&start_year=${currentYear}&num_months=12`);
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
  }, []);

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
      <div className="special-days-layout">
        <div className="year-grid">
          {yearData?.map((month) => (
            <div key={`${month.year}-${month.month}`} className="mini-month">
              <div className="mini-month__header">
                {month.month_name} {month.year}
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
          <h3>Tag Assignment</h3>
          <p>{selectedDates.length} days selected</p>
          
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
            <select value={formWhere} onChange={(e) => setFormWhere(e.target.value)}>
              <option value="">None</option>
              {tagsConfig?.where.map(tag => (
                <option key={tag.id} value={tag.id}>{tag.label}</option>
              ))}
            </select>
          </div>

          <button className="btn btn--primary" onClick={handleAssign} disabled={selectedDates.length === 0}>
            Apply Tags
          </button>

          <hr className="divider" />

          <div className="tag-management">
            <h3>Manage Tags</h3>
            <div className="form-section">
              <label>Primary Categories</label>
              <div className="tag-list-edit">
                {tagsConfig?.primary.map(tag => (
                  <div key={tag.id} className="tag-edit-item">
                    <div className="tag-dot" style={{ backgroundColor: tag.color }} />
                    <span>{tag.label}</span>
                    <button className="icon-btn" onClick={() => removeTag('primary', tag.id)}><Trash2 size={14} /></button>
                  </div>
                ))}
                <div className="tag-add-row">
                  <input type="text" placeholder="New tag..." id="new-primary-label" />
                  <input type="color" id="new-primary-color" defaultValue="#3b82f6" />
                  <button className="icon-btn" onClick={() => addTag('primary')}><Plus size={16} /></button>
                </div>
              </div>
            </div>

            <div className="form-section">
              <label>Locations (Where)</label>
              <div className="tag-list-edit">
                {tagsConfig?.where.map(tag => (
                  <div key={tag.id} className="tag-edit-item">
                    <div className="tag-dot" style={{ backgroundColor: tag.color }} />
                    <span>{tag.label}</span>
                    <button className="icon-btn" onClick={() => removeTag('where', tag.id)}><Trash2 size={14} /></button>
                  </div>
                ))}
                <div className="tag-add-row">
                  <input type="text" placeholder="New location..." id="new-where-label" />
                  <input type="color" id="new-where-color" defaultValue="#64748b" />
                  <button className="icon-btn" onClick={() => addTag('where')}><Plus size={16} /></button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
