import { BrowserRouter } from 'react-router-dom';
import { AppInitializer } from './components/AppInitializer/AppInitializer';
import { AppRoutes } from './components/AppRoutes/AppRoutes';
import { ThemeApplier } from './components/ThemeApplier/ThemeApplier';
import { APP_BASENAME } from './config';
import styles from './App.module.scss';

function App() {
  return (
    <AppInitializer>
      <ThemeApplier />
      <BrowserRouter basename={APP_BASENAME}>
        <div className={styles.app}>
          <AppRoutes />
        </div>
      </BrowserRouter>
    </AppInitializer>
  );
}

export default App;
