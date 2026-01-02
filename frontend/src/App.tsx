import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import JobDetails from './pages/JobDetails';
import CreateJob from './pages/CreateJob';
import Settings from './pages/Settings';

export interface Toast {
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning';
}

function App() {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((message: string, type: Toast['type'] = 'success') => {
        const id = Date.now().toString();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 5000);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard addToast={addToast} />} />
                    <Route path="/jobs" element={<Jobs addToast={addToast} />} />
                    <Route path="/jobs/:jobId" element={<JobDetails addToast={addToast} />} />
                    <Route path="/create-job" element={<CreateJob addToast={addToast} />} />
                    <Route path="/settings" element={<Settings />} />
                </Routes>
            </Layout>

            {/* Toast Container */}
            <div className="toast-container">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        className={`toast toast-${toast.type}`}
                        onClick={() => removeToast(toast.id)}
                    >
                        {toast.message}
                    </div>
                ))}
            </div>
        </BrowserRouter>
    );
}

export default App;
