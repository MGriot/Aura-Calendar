import { Calendar, ChevronLeft, ChevronRight, Settings } from 'lucide-react';

import { useEffect, useState } from 'react';

export default function Header({
  rangeLabel,
  onPrev,
  onNext,
  onOpenSettings,
  activeTab,
  setActiveTab,
  reloadInterval,
  lastFetch,
}) {
  const [countdown, setCountdown] = useState('');

  useEffect(() => {
    if (!reloadInterval || !lastFetch) {
      setCountdown('');
      return;
    }
    const ms = reloadInterval * 60 * 1000;
    const update = () => {
      const diff = ms - (Date.now() - lastFetch);
      if (diff <= 0) {
        setCountdown('Updating…');
        return;
      }
      const s = Math.floor(diff / 1000);
      const m = Math.floor(s / 60);
      const sec = s % 60;
      setCountdown(`${m}m ${sec}s`);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [reloadInterval, lastFetch]);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'month', label: 'Month' },
    { id: 'week', label: 'Week' },
    { id: 'events', label: 'Events' },
    { id: 'special_days', label: 'Special Days' },
  ];

  return (
    <header className="header" id="app-header">
      <div className="header__left">
        <Calendar className="header__icon" size={22} />
        <h1 className="header__title">Aura</h1>
      </div>

      <div className="header__tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-link ${activeTab === tab.id ? 'tab-link--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            id={`tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab !== 'special_days' && (
        <nav className="header__nav" aria-label={activeTab === 'week' ? 'Week navigation' : 'Month navigation'}>
          <button
            className="nav-btn"
            onClick={onPrev}
            aria-label={activeTab === 'week' ? 'Previous week' : 'Previous 4 months'}
            id="nav-prev"
          >
            <ChevronLeft size={18} />
          </button>
          <span className="header__range">{rangeLabel}</span>
          <button
            className="nav-btn"
            onClick={onNext}
            aria-label={activeTab === 'week' ? 'Next week' : 'Next 4 months'}
            id="nav-next"
          >
            <ChevronRight size={18} />
          </button>
        </nav>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {reloadInterval > 0 && (
          <div className="auto-reload-timer" title="Auto-reload status">
            <small style={{ fontSize: '0.8rem' }}>Auto: {countdown || '—'}</small>
          </div>
        )}

        <button
          className="settings-btn"
          onClick={onOpenSettings}
          aria-label="Open settings"
          id="settings-btn"
        >
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </header>
  );
}
