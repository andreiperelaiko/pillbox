import { BrowserRouter } from 'react-router-dom';
import { AppInitializer } from './components/AppInitializer/AppInitializer';
import { AppRoutes } from './components/AppRoutes/AppRoutes';
import styles from './App.module.scss';

function App() {
  return (
    <AppInitializer>
      <BrowserRouter>
        <div className={styles.app}>
          <AppRoutes />
        </div>
      </BrowserRouter>
    </AppInitializer>
  );
}

export default App;
