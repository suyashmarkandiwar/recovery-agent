import React from 'react';

export default function MetricsCards({ financials }) {
  const { total_recovered = 0, total_at_risk = 0, total_written_off = 0 } = financials || {};

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const Card = ({ title, amount, colorClass, highlight }) => (
    <div style={{
      flex: '1',
      minWidth: '250px',
      padding: '24px',
      background: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(10px)',
      WebkitBackdropFilter: 'blur(10px)',
      borderRadius: '16px',
      border: `1px solid ${highlight ? colorClass : 'rgba(255, 255, 255, 0.1)'}`,
      boxShadow: highlight ? `0 0 20px ${colorClass}20` : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <h3 style={{ margin: 0, color: '#94a3b8', fontSize: '14px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {title}
      </h3>
      <div style={{ margin: 0, color: '#f8fafc', fontSize: '32px', fontWeight: '700' }}>
        {formatCurrency(amount)}
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '32px' }}>
      <Card 
        title="Total Recovered" 
        amount={total_recovered} 
        colorClass="#10b981" 
        highlight={true} 
      />
      <Card 
        title="Revenue at Risk" 
        amount={total_at_risk} 
        colorClass="#f59e0b" 
      />
      <Card 
        title="Written Off" 
        amount={total_written_off} 
        colorClass="#ef4444" 
      />
    </div>
  );
}
