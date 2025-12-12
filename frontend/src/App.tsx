import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation/Navigation';
import { AppInitializer } from './components/AppInitializer/AppInitializer';
import { HomePage } from './pages/HomePage/HomePage';
import { MedicationsPage } from './pages/MedicationsPage/MedicationsPage';
import { CaregiversPage } from './pages/CaregiversPage/CaregiversPage';
import { SettingsPage } from './pages/SettingsPage/SettingsPage';
import styles from './App.module.scss';

function App() {
  return (
    <AppInitializer>
      <BrowserRouter>
        <div className={styles.app}>
          <Navigation />
          <main className={styles.main}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/medications" element={<MedicationsPage />} />
              <Route path="/caregivers" element={<CaregiversPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AppInitializer>
  );
}

export default App;
