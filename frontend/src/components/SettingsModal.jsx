import { useState, useEffect } from 'react';
import { X, Upload, Eye, Check, AlertCircle, Sun, Moon } from 'lucide-react';

export default function SettingsModal({ onClose, onSaved, theme, setTheme }) {
  const [settings, setSettings] = useState({
    csv_path: '',
    col_start_date: 'start_date',
    col_end_date: 'end_date',
    col_event_name: 'event_name',
    col_category: 'category',
    date_format: '%Y-%m-%d',
    color_map: {},
    enable_advanced_calendar: false,
    advanced_countries: ['IT', 'US'],
    show_special_days: true,
    enabled_cultural_calendars: ['holidays', 'lunar', 'hebrew', 'islamic'],
    reload_interval: 0,
    external_url: '',
  });
  const [headers, setHeaders] = useState([]);
  const [preview, setPreview] = useState([]);
  const [uniqueCategories, setUniqueCategories] = useState([]);
  const [status, setStatus] = useState(null); // { type: 'success'|'error', msg }
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Load current settings on mount
  useEffect(() => {
    fetch('/api/settings')
      .then((r) => r.json())
      .then((data) => setSettings(prev => ({ ...prev, ...data })))
      .catch(() => {});
  }, []);

  // Sync unique categories from preview
  useEffect(() => {
    if (preview.length > 0 && settings.col_category) {
      const cats = Array.from(new Set(preview.map(row => row[settings.col_category]).filter(Boolean)));
      setUniqueCategories(cats);
      
      const newMap = { ...settings.color_map };
      let changed = false;
      const palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];
      
      cats.forEach((cat, i) => {
        if (!newMap[cat]) {
          newMap[cat] = palette[i % palette.length];
          changed = true;
        }
      });
      if (changed) setSettings(s => ({ ...s, color_map: newMap }));
    }
  }, [preview, settings.col_category]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      update('csv_path', data.path);
      setStatus({ type: 'success', msg: `Uploaded ${file.filename || file.name}` });
      // Auto-preview
      setTimeout(() => previewCSV(), 100);
    } catch (err) {
      setStatus({ type: 'error', msg: 'Failed to upload file' });
    } finally {
      setUploading(false);
    }
  };

  const previewCSV = async () => {
    const path = settings.csv_path || settings.external_url;
    if (!path) return;
    setStatus(null);
    try {
      const res = await fetch(
        `/api/csv/preview?path=${encodeURIComponent(path)}`,
      );
      if (!res.ok) {
        const err = await res.json();
        setStatus({ type: 'error', msg: err.detail });
        return;
      }
      const data = await res.json();
      setHeaders(data.headers);
      setPreview(data.preview_rows);
      setStatus({ type: 'success', msg: `Found ${data.headers.length} columns` });
    } catch {
      setStatus({ type: 'error', msg: 'Could not reach the server' });
    }
  };

  const save = async () => {
    setSaving(true);
    setStatus(null);
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      const data = await res.json();
      
      const eventMsg = settings.csv_path 
        ? `${data.events_loaded} events loaded.`
        : 'Settings updated (No CSV linked).';
        
      setStatus({
        type: 'success',
        msg: `Configuration Saved! ${eventMsg}`,
      });
      setTimeout(() => onSaved(), 1000);
    } catch {
      setStatus({ type: 'error', msg: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const update = (key, val) => setSettings((s) => ({ ...s, [key]: val }));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} id="settings-modal">
        <div className="modal__header">
          <h2 className="modal__title">
            <Upload size={20} /> Event Settings
          </h2>
          <div className="modal__header-actions">
            <button
              className="theme-toggle"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              id="theme-toggle-btn"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="modal__close" onClick={onClose} aria-label="Close">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="modal__body">
          <div className="settings-grid">
            {/* Column 1: Sources */}
            <div className="settings-section">
              <h3 className="section-title">Data Source</h3>
              
              <div className="field">
                <label className="field__label">Upload Local File</label>
                <div 
                  className={`dropzone ${uploading ? 'dropzone--uploading' : ''}`}
                  onClick={() => document.getElementById('file-upload').click()}
                >
                  <input 
                    type="file" 
                    id="file-upload" 
                    hidden 
                    accept=".csv" 
                    onChange={handleFileUpload}
                  />
                  <Upload size={24} />
                  <p>{uploading ? 'Uploading...' : 'Click or Drag CSV here'}</p>
                </div>
              </div>

              <div className="field">
                <label className="field__label">Remote URL or Host Path</label>
                <input
                  className="field__input"
                  type="text"
                  value={settings.external_url}
                  onChange={(e) => update('external_url', e.target.value)}
                  placeholder="https://... or C:\path\to\file.csv"
                  id="input-external-url"
                />
                <span className="field__hint">Use this for files outside the Docker container.</span>
              </div>

              <div className="field">
                <label className="field__label">Active Path (Internal)</label>
                <div className="field__row">
                  <input
                    className="field__input"
                    type="text"
                    value={settings.csv_path}
                    readOnly
                    placeholder="Container path will appear here"
                    id="input-csv-path"
                  />
                  <button className="btn btn--secondary" onClick={previewCSV} title="Preview Data">
                    <Eye size={16} /> Preview
                  </button>
                </div>
              </div>
            </div>

            {/* Column 2: Configuration */}
            <div className="settings-section">
              <h3 className="section-title">Formatting</h3>
              <div className="field">
                <label className="field__label">Date Format</label>
                <input
                  className="field__input"
                  type="text"
                  value={settings.date_format}
                  onChange={(e) => update('date_format', e.target.value)}
                  placeholder="%Y-%m-%d"
                  id="input-date-format"
                />
                <span className="field__hint">Python strftime format (e.g. %Y-%m-%d)</span>
              </div>
              
              <div className="field">
                <label className="field__label">Auto-Reload Frequency</label>
                <select
                  className="field__select"
                  value={settings.reload_interval}
                  onChange={(e) => update('reload_interval', parseInt(e.target.value))}
                  id="select-reload-interval"
                >
                  <option value={0}>Manual Refresh Only</option>
                  <option value={5}>Every 5 Minutes</option>
                  <option value={15}>Every 15 Minutes</option>
                  <option value={30}>Every 30 Minutes</option>
                  <option value={60}>Every Hour</option>
                </select>
              </div>
            </div>
          </div>
          
          <fieldset className="fieldset">
            <legend className="fieldset__legend">Calendar Metadata Components</legend>
            <div className="cultural-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {[
                { id: 'holidays_it', label: 'Italy Holidays (IT)' },
                { id: 'holidays_us', label: 'USA Holidays (US)' },
                { id: 'holidays_mx', label: 'Mexico Holidays (MX)' },
                { id: 'holidays_cz', label: 'Czech Republic (CZ)' },
                { id: 'catholic', label: 'Catholic (Liturgical)' },
                { id: 'chinese', label: 'Chinese (Lunar Festivals)' },
                { id: 'hebrew', label: 'Hebrew Calendar' },
                { id: 'islamic', label: 'Islamic (Hijri) Calendar' },
                { id: 'lunar', label: 'Lunar Dates (L:M/D)' },
              ].map(cal => (
                <label key={cal.id} className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={(settings.enabled_cultural_calendars || []).includes(cal.id)}
                    onChange={(e) => {
                      const current = settings.enabled_cultural_calendars || [];
                      const next = e.target.checked 
                        ? [...current, cal.id]
                        : current.filter(id => id !== cal.id);
                      update('enabled_cultural_calendars', next);
                    }}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <span style={{ fontSize: '0.85rem' }}>{cal.label}</span>
                </label>
              ))}
            </div>
            
            <div className="field" style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
              <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={settings.show_special_days ?? true}
                  onChange={(e) => update('show_special_days', e.target.checked)}
                  style={{ width: '18px', height: '18px' }}
                />
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Show User-cast Special Days markers</span>
              </label>
            </div>
          </fieldset>

          {/* Column Mapping */}
          {headers.length > 0 && (
            <fieldset className="fieldset">
              <legend className="fieldset__legend">Column Mapping</legend>
              <div className="field-grid">
                {[
                  ['col_start_date', 'Start Date Column (Required)'],
                  ['col_end_date', 'End Date Column (Optional)'],
                  ['col_event_name', 'Event Name to Display'],
                  ['col_category', 'Color Legend Column (Type/Category)'],
                ].map(([key, label]) => (
                  <div className="field" key={key}>
                    <label className="field__label">{label}</label>
                    <select
                      className="field__select"
                      value={settings[key]}
                      onChange={(e) => update(key, e.target.value)}
                      id={`select-${key}`}
                    >
                      <option value="">— select —</option>
                      {headers.map((h) => (
                        <option key={h} value={h}>{h}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </fieldset>
          )}

          {/* Color Mapping */}
          {uniqueCategories.length > 0 && (
            <fieldset className="fieldset">
              <legend className="fieldset__legend">Color Legend Overrides</legend>
              <div className="color-grid">
                {uniqueCategories.map(cat => (
                  <div className="color-item" key={cat}>
                    <span className="color-item__label">{cat}</span>
                    <input 
                      type="color" 
                      className="color-item__input"
                      value={settings.color_map[cat] || '#3b82f6'}
                      onChange={(e) => {
                        const newMap = { ...settings.color_map, [cat]: e.target.value };
                        update('color_map', newMap);
                      }}
                    />
                  </div>
                ))}
              </div>
            </fieldset>
          )}

          {/* CSV Preview Table */}
          {preview.length > 0 && (
            <div className="preview-table-wrap">
              <table className="preview-table">
                <thead>
                  <tr>
                    {headers.map((h) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i}>
                      {headers.map((h) => (
                        <td key={h}>{row[h]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Status */}
          {status && (
            <div className={`status status--${status.type}`}>
              {status.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
              {status.msg}
            </div>
          )}
        </div>

        <div className="modal__footer">
          <button className="btn btn--ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn--primary" onClick={save} disabled={saving} id="btn-save-settings">
            {saving ? 'Saving…' : 'Save & Load Events'}
          </button>
        </div>
      </div>
    </div>
  );
}
