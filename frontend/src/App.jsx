import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header.jsx';
import MonthGrid from './components/MonthGrid.jsx';
import SettingsModal from './components/SettingsModal.jsx';
import DashboardView from './components/DashboardView.jsx';
import WeekView from './components/WeekView.jsx';
import EventListView from './components/EventListView.jsx';
import DayDetailsModal from './components/DayDetailsModal.jsx';
import SpecialDaysView from './components/SpecialDaysView.jsx';

const TODAY = new Date().toISOString().split('T')[0];

export default function App() {
  const now = new Date();
  const [startMonth, setStartMonth] = useState(() => Number(sessionStorage.getItem('aura-month')) || now.getMonth() + 1);
  const [startYear, setStartYear] = useState(() => Number(sessionStorage.getItem('aura-year')) || now.getFullYear());
  const [startDay, setStartDay] = useState(() => Number(sessionStorage.getItem('aura-day')) || now.getDate());
  const [lastFetch, setLastFetch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('aura-theme') || 'dark');
  const [activeTab, setActiveTab] = useState(() => sessionStorage.getItem('aura-tab') || 'month');
  const [months, setMonths] = useState(null);
  const [allEvents, setAllEvents] = useState([]);
  const [settings, setSettings] = useState(null);
  const [tagsConfig, setTagsConfig] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);

  // Persist state to prevent resets
  useEffect(() => { sessionStorage.setItem('aura-month', startMonth); }, [startMonth]);
  useEffect(() => { sessionStorage.setItem('aura-year', startYear); }, [startYear]);
  useEffect(() => { sessionStorage.setItem('aura-tab', activeTab); }, [activeTab]);
  useEffect(() => { sessionStorage.setItem('aura-day', startDay); }, [startDay]);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('aura-theme', theme);
  }, [theme]);

  const fetchCalendar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/calendar?start_month=${startMonth}&start_year=${startYear}&num_months=4`,
      );
      const data = await res.json();
      setMonths(data.months);
      setAllEvents(data.events || []);
      
      // Ensure all requested components are enabled if missing
      const updatedSettings = { ...data.settings };
      if (updatedSettings && !updatedSettings.enabled_cultural_calendars) {
        updatedSettings.enabled_cultural_calendars = ['holidays', 'chinese', 'catholic'];
      }
      
      setSettings(updatedSettings);
      setTagsConfig(data.tags_config);
    } catch (err) {
      console.error('Failed to fetch calendar:', err);
    } finally {
      setLoading(false);
    }
  }, [startMonth, startYear]);

  useEffect(() => {
    fetchCalendarWithTimestamp();
  }, [fetchCalendarWithTimestamp]);

  // update lastFetch timestamp when calendar is fetched
  const fetchCalendarWithTimestamp = useCallback(async () => {
    await fetchCalendar();
    setLastFetch(Date.now());
  }, [fetchCalendar]);

  // Auto-reload polling
  useEffect(() => {
    if (settings?.reload_interval > 0) {
      const ms = settings.reload_interval * 60 * 1000;
      const timer = setInterval(() => {
        fetchCalendarWithTimestamp();
      }, ms);
      return () => clearInterval(timer);
    }
  }, [settings?.reload_interval, fetchCalendarWithTimestamp]);

  const navigate = (direction) => {
    if (activeTab === 'week') {
      // move by weeks
      const dt = new Date(startYear, startMonth - 1, startDay);
      dt.setDate(dt.getDate() + direction * 7);
      setStartYear(dt.getFullYear());
      setStartMonth(dt.getMonth() + 1);
      setStartDay(dt.getDate());
      sessionStorage.setItem('aura-day', dt.getDate());
    } else {
      let m = startMonth + direction * 4;
      let y = startYear;
      while (m > 12) { m -= 12; y++; }
      while (m < 1) { m += 12; y--; }
      setStartMonth(m);
      setStartYear(y);
    }
  };

  const getWeekNumber = (d) => {
    // ISO week number
    const date = new Date(d.getTime());
    date.setHours(0,0,0,0);
    // Thursday in current week decides the year.
    date.setDate(date.getDate() + 3 - ((date.getDay() + 6) % 7));
    const week1 = new Date(date.getFullYear(), 0, 4);
    return 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7);
  };

  const rangeLabel = (() => {
    if (activeTab === 'week') {
      const anchor = new Date(startYear, startMonth - 1, startDay);
      const w = getWeekNumber(anchor);
      return `Week ${w} ${anchor.getFullYear()}`;
    }
    return months
      ? `${months[0].month_name.slice(0, 3)} – ${months[months.length - 1].month_name.slice(0, 3)} ${months[months.length - 1].year}`
      : '';
  })();

  return (
    <div className="app">
      {/* Decorative background orbs */}
      <div className="bg-orb bg-orb--1" />
      <div className="bg-orb bg-orb--2" />
      <div className="bg-orb bg-orb--3" />

      <Header
        rangeLabel={rangeLabel}
        onPrev={() => navigate(-1)}
        onNext={() => navigate(1)}
        onOpenSettings={() => setShowSettings(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        reloadInterval={settings?.reload_interval}
        lastFetch={lastFetch}
      />

      <main className="calendar-content">
        {loading && !months && (
          <div className="loader">
            <div className="loader-spinner" />
          </div>
        )}

        {!loading && activeTab === 'dashboard' && (
          <DashboardView settings={settings} />
        )}

        {activeTab === 'month' && months && (
          <div className="calendar-grid" id="calendar-grid">
            {months.map((m) => (
              <MonthGrid 
                key={`${m.year}-${m.month}`} 
                month={m} 
                today={TODAY} 
                allEvents={allEvents}
                settings={settings}
                tagsConfig={tagsConfig}
                onDayClick={(day) => setSelectedDay(day)}
              />
            ))}
          </div>
        )}

        {!loading && activeTab === 'week' && (
          <WeekView 
            onDayClick={(day) => setSelectedDay(day)} 
            startYear={startYear}
            startMonth={startMonth}
              startDay={startDay}
              settings={settings}
              tagsConfig={tagsConfig}
            />
        )}

        {!loading && activeTab === 'events' && (
          <EventListView allEvents={allEvents} settings={settings} />
        )}

        {activeTab === 'special_days' && (
          <SpecialDaysView settings={settings} />
        )}
      </main>

      {showSettings && (
        <SettingsModal
          onClose={() => setShowSettings(false)}
          theme={theme}
          setTheme={setTheme}
          onSaved={() => {
            setShowSettings(false);
            fetchCalendar();
          }}
        />
      )}

      {selectedDay && (
        <DayDetailsModal 
          day={selectedDay}
          tagsConfig={tagsConfig}
          onClose={() => setSelectedDay(null)}
          colorMap={settings?.color_map}
          eventTemplate={settings?.event_card_template}
        />
      )}
    </div>
  );
}
