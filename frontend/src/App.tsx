import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import AdminPage from './pages/AdminPage';
import CreatePollPage from './pages/CreatePollPage';
import NotFoundPage from './pages/NotFoundPage';
import PollPage from './pages/PollPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CreatePollPage />} />
        <Route path="p/:pollId" element={<PollPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
