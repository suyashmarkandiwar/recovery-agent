import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import MetricsCards from '../components/MetricsCards';
import InvoiceTable from '../components/InvoiceTable';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [showNotification, setShowNotification] = useState(false);
  const [latestScanTime, setLatestScanTime] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkScanStatus = async () => {
      try {
        const data = await apiClient('/api/analytics/last-scan-time');
        if (data && data.last_scan_time) {
          const serverScanTime = data.last_scan_time;
          const seenScanTime = localStorage.getItem('LAST_SEEN_SCAN_TIME');
          
          if (!seenScanTime || serverScanTime > seenScanTime) {
            setShowNotification(true);
            setLatestScanTime(serverScanTime);
          }
        }
      } catch (err) {
        console.error('Failed to check scan status', err);
      }
    };

    checkScanStatus(); // Check immediately on mount
    const interval = setInterval(checkScanStatus, 15000); // Check every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const handleCloseNotification = () => {
    if (latestScanTime) {
      localStorage.setItem('LAST_SEEN_SCAN_TIME', latestScanTime);
    }
    setShowNotification(false);
  };

  const fetchDashboardData = async () => {
    try {
      const [statsRes, invoicesRes] = await Promise.all([
        apiClient('/api/analytics/recovery-stats'),
        apiClient('/api/invoices/')
      ]);
      setStats(statsRes.data);
      setInvoices(invoicesRes.data);
      setLoading(false);
    } catch (err) {
      if (err.status === 401) {
        navigate('/login');
      } else {
        console.error("Dashboard fetch failed:", err);
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [navigate]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontFamily: 'sans-serif' }}>
        Loading dashboard...
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#f8fafc',
      fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Top Navbar */}
      <header style={{
        padding: '16px 32px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)'
      }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600', letterSpacing: '-0.5px' }}>
          Recovery Agent
        </h1>
        <button
          onClick={async () => {
            try { await apiClient('/api/auth/logout', { method: 'POST' }); } catch (e) { }
            navigate('/login');
          }}
          style={{
            padding: '8px 16px',
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.2)',
            color: '#e2e8f0',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            transition: 'background 0.2s'
          }}
          onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
          onMouseOut={(e) => e.target.style.background = 'transparent'}
        >
          Logout
        </button>
      </header>

      {/* Main Content */}
      <main style={{ padding: '32px', maxWidth: '100%', margin: '0 10px' }}>
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>Overview</h2>
          <p style={{ margin: 0, color: '#94a3b8' }}>Real-time metrics for your automated recovery batch.</p>
        </div>

        {/* Phase 3: Metrics */}
        {stats && <MetricsCards financials={stats.financials} />}

        {/* Phase 4 & 5: Invoice Table with Actions */}
        <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '600' }}>Invoices</h2>
        </div>
        <InvoiceTable invoices={invoices} onRefresh={fetchDashboardData} />
      </main>

      {/* Toast Notification */}
      {showNotification && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: 'rgba(30, 41, 59, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(59, 130, 246, 0.5)',
          borderRadius: '8px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '16px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          zIndex: 9999,
          maxWidth: '350px'
        }}>
          <div>
            <h4 style={{ margin: '0 0 6px 0', fontSize: '15px', color: '#f8fafc' }}>Scan Complete</h4>
            <p style={{ margin: 0, fontSize: '13px', color: '#cbd5e1', lineHeight: '1.4' }}>
              The AI recovery agent has successfully finished scanning and processing the overdue invoices.
            </p>
          </div>
          <button 
            onClick={handleCloseNotification}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '18px',
              lineHeight: '1',
              padding: '0 4px',
              fontWeight: 'bold'
            }}
            onMouseOver={e => e.target.style.color = '#f8fafc'}
            onMouseOut={e => e.target.style.color = '#94a3b8'}
          >
            &times;
          </button>
        </div>
      )}
    </div>
  );
}
