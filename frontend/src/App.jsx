import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Splash from "./pages/common/Splash";
import RoleSelection from "./pages/common/RoleSelection";

import Register from "./pages/user/Register";
import UserLogin from "./pages/user/Login";
import UserDashboard from "./pages/user/Dashboard";
import ScanProduct from "./pages/user/ScanProduct";
import ScanHistory from "./pages/user/ScanHistory";
import FileComplaint from "./pages/user/FileComplaint";

import OfficerLogin from "./pages/officer/OfficerLogin";
import OfficerDashboard from "./pages/officer/OfficerDashboard";

import FoodLabelScanner from "./pages/food/FoodLabelScanner";

// Guard: redirects unauthenticated users to the login page
function ProtectedUserRoute({ children }) {
  const token = localStorage.getItem("token");
  if (!token) {
    return <Navigate to="/user/login" replace />;
  }
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Onboarding & Common */}
        <Route path="/" element={<Splash />} />
        <Route path="/roles" element={<RoleSelection />} />

        {/* Food Label FSSAI Analyzer */}
        <Route path="/food-scan" element={<FoodLabelScanner />} />

        {/* User Portal — login & register are public */}
        <Route path="/user/login" element={<UserLogin />} />
        <Route path="/user/register" element={<Register />} />

        {/* User Portal — protected pages require a token */}
        <Route
          path="/user/dashboard"
          element={
            <ProtectedUserRoute>
              <UserDashboard />
            </ProtectedUserRoute>
          }
        />
        <Route
          path="/user/scan"
          element={
            <ProtectedUserRoute>
              <ScanProduct />
            </ProtectedUserRoute>
          }
        />
        <Route
          path="/user/history"
          element={
            <ProtectedUserRoute>
              <ScanHistory />
            </ProtectedUserRoute>
          }
        />
        <Route
          path="/user/complaint"
          element={
            <ProtectedUserRoute>
              <FileComplaint />
            </ProtectedUserRoute>
          }
        />

        {/* Officer / Inspector Portal */}
        <Route path="/officer/login" element={<OfficerLogin />} />
        <Route path="/officer/dashboard" element={<OfficerDashboard />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;