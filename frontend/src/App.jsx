import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Equipment from './pages/Equipment';
import MaintenanceLogs from './pages/MaintenanceLogs';
import SensorData from './pages/SensorData';
import FailureReports from './pages/FailureReports';
import SpareParts from './pages/SpareParts';
import Upload from './pages/Upload';
import MaintenanceAssistant from './pages/MaintenanceAssistant';
import DocumentLibrary from './pages/DocumentLibrary';
import EquipmentHealth from './pages/EquipmentHealth';
import AlertCenter from './pages/AlertCenter';
import SensorTrends from './pages/SensorTrends';
import PredictiveDashboard from './pages/PredictiveMaintenance/Dashboard';
import RootCauseAnalysis from './pages/RootCauseAnalysis';
import MaintenanceRecommendations from './pages/MaintenanceRecommendations';
import ProcurementInventory from './pages/ProcurementInventory';
import DecisionSupport from './pages/DecisionSupport';
import LearningAnalytics from './pages/LearningAnalytics';

import DocumentIntelligence from './pages/DocumentIntelligence';

import InputIntelligenceCenter from './pages/InputIntelligenceCenter';
import OperationalData from './pages/OperationalData';
import HomePage from './pages/HomePage';
import LandingPage from './pages/LandingPage';

function App() {
  return (
    <Routes>
      {/* Landing page — no sidebar */}
      <Route path="/" element={<LandingPage />} />

      {/* App with sidebar */}
      <Route path="/" element={<Layout />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="equipment" element={<Equipment />} />
        <Route path="maintenance-logs" element={<MaintenanceLogs />} />
        <Route path="sensor-data" element={<SensorData />} />
        <Route path="failure-reports" element={<FailureReports />} />
        <Route path="spare-parts" element={<SpareParts />} />
        <Route path="upload" element={<Upload />} />
        <Route path="assistant" element={<MaintenanceAssistant />} />
        <Route path="documents" element={<DocumentLibrary />} />
        <Route path="equipment-health" element={<EquipmentHealth />} />
        <Route path="alerts" element={<AlertCenter />} />
        <Route path="sensor-trends" element={<SensorTrends />} />
        <Route path="predictive" element={<PredictiveDashboard />} />
        <Route path="root-cause" element={<RootCauseAnalysis />} />
        <Route path="recommendations" element={<MaintenanceRecommendations />} />
        <Route path="procurement" element={<ProcurementInventory />} />
        <Route path="decision-support" element={<DecisionSupport />} />
        <Route path="learning" element={<LearningAnalytics />} />
        <Route path="doc-intelligence" element={<DocumentIntelligence />} />
        <Route path="operational" element={<OperationalData />} />
        <Route path="intelligence-hub" element={<InputIntelligenceCenter />} />
      </Route>
    </Routes>
  );
}

export default App;