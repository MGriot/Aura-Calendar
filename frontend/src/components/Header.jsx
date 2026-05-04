import { Calendar, ChevronLeft, ChevronRight, Settings } from 'lucide-react';

export default function Header({
  rangeLabel,
  onPrev,
  onNext,
  onOpenSettings,
  activeTab,
  setActiveTab,
}) {
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

      <nav className="header__nav" aria-label="Month navigation">
        <button
          className="nav-btn"
          onClick={onPrev}
          aria-label="Previous 4 months"
          id="nav-prev"
        >
          <ChevronLeft size={18} />
        </button>
        <span className="header__range">{rangeLabel}</span>
        <button
          className="nav-btn"
          onClick={onNext}
          aria-label="Next 4 months"
          id="nav-next"
        >
          <ChevronRight size={18} />
        </button>
      </nav>

      <button
        className="settings-btn"
        onClick={onOpenSettings}
        aria-label="Open settings"
        id="settings-btn"
      >
        <Settings size={18} />
        <span>Settings</span>
      </button>
    </header>
  );
}
