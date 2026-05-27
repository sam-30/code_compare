import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import HistoryPage from "./pages/HistoryPage";
import LoginPage from "./pages/LoginPage";
import NewComparisonPage from "./pages/NewComparisonPage";
import RegisterPage from "./pages/RegisterPage";
import ResultsPage from "./pages/ResultsPage";

export default function App() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route path="register" element={<RegisterPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<NewComparisonPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="comparisons/:id" element={<ResultsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
