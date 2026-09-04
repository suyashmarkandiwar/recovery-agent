import React, { useState } from 'react';
import { apiClient } from '../api/client';

export default function InvoiceTable({ invoices, onRefresh }) {
  const [actingOn, setActingOn] = useState(null);
  const [recentlySent, setRecentlySent] = useState(null);
  const [negotiatingDateFor, setNegotiatingDateFor] = useState(null);
  const [proposedDate, setProposedDate] = useState('');

  if (!invoices || invoices.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '12px' }}>
        No invoices found in the system.
      </div>
    );
  }

  const handleResendLink = async (id) => {
    setActingOn(id);
    try {
      await apiClient(`/api/invoices/${id}/resend-link`, { method: 'POST' });
      if (onRefresh) await onRefresh();
      setRecentlySent(id);
      setTimeout(() => setRecentlySent(null), 3000);
    } catch (err) {
      alert(`Failed to resend link: ${err.message}`);
    } finally {
      setActingOn(null);
    }
  };

  const handleSaveDate = async (id) => {
    if (!proposedDate) return;
    setActingOn(id);
    try {
      await apiClient(`/api/invoices/${id}/negotiated-date`, {
        method: 'PATCH',
        body: { proposed_date: proposedDate }
      });
      if (onRefresh) await onRefresh();
      setNegotiatingDateFor(null);
      setProposedDate('');
    } catch (err) {
      alert(`Failed to save date: ${err.message}`);
    } finally {
      setActingOn(null);
    }
  };

  const handleWriteOff = async (id, outcome) => {
    setActingOn(id);
    try {
      await apiClient(`/api/invoices/${id}/write-off`, {
        method: 'PATCH',
        body: { outcome }
      });
      if (onRefresh) await onRefresh();
    } catch (err) {
      alert(`Failed to write off: ${err.message}`);
    } finally {
      setActingOn(null);
    }
  };

  const formatCurrency = (amount) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);

  const formatDate = (dateString) => {
    if (!dateString) return <span style={{ color: '#475569' }}>—</span>;
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case 'PAID': return { bg: 'rgba(16, 185, 129, 0.2)', text: '#34d399' };
      case 'OVERDUE': return { bg: 'rgba(245, 158, 11, 0.2)', text: '#fbbf24' };
      case 'BAD_DEBT':
      case 'LEGAL': return { bg: 'rgba(239, 68, 68, 0.2)', text: '#f87171' };
      default: return { bg: 'rgba(148, 163, 184, 0.2)', text: '#cbd5e1' };
    }
  };

  const TH = ({ children }) => (
    <th style={{
      padding: '14px 16px',
      color: '#64748b',
      fontSize: '11px',
      fontWeight: '700',
      textTransform: 'uppercase',
      letterSpacing: '0.6px',
      whiteSpace: 'nowrap',
      borderBottom: '1px solid rgba(255,255,255,0.08)',
      backgroundColor: 'rgba(0,0,0,0.25)'
    }}>
      {children}
    </th>
  );

  const TD = ({ children, style = {} }) => (
    <td style={{
      padding: '14px 16px',
      color: '#cbd5e1',
      fontSize: '13px',
      borderBottom: '1px solid rgba(255,255,255,0.04)',
      verticalAlign: 'middle',
      ...style
    }}>
      {children}
    </td>
  );

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.6)',
      backdropFilter: 'blur(10px)',
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      overflow: 'hidden'
    }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr>
              <TH># Invoice ID</TH>
              <TH>Client Name</TH>
              <TH>Client Email</TH>
              <TH>Client Phone</TH>
              <TH>Amount</TH>
              <TH>Due Date</TH>
              <TH>Days Passed</TH>
              <TH>Last Contacted</TH>
              <TH>Paused Until</TH>
              <TH>Status</TH>
              <TH>Razorpay Link</TH>
              <TH>Requires Call</TH>
              <TH>Actions</TH>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => {
              const statusStyle = getStatusStyle(inv.status);
              const isActing = actingOn === inv.id;
              const isPausedActive = inv.pause_followups_until && new Date(inv.pause_followups_until) > new Date();

              return (
                <tr
                  key={inv.id}
                  style={{ transition: 'background-color 0.15s' }}
                  onMouseOver={e => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)'}
                  onMouseOut={e => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  {/* 0. Invoice ID */}
                  <TD style={{ color: '#475569', fontWeight: '600', fontFamily: 'monospace' }}>#{inv.id}</TD>

                  {/* 1. Client Name */}
                  <TD style={{ color: '#f8fafc', fontWeight: '500' }}>
                    {inv.client_name}
                  </TD>

                  {/* 2. Client Email */}
                  <TD>{inv.client_email}</TD>

                  {/* 3. Client Phone */}
                  <TD>{inv.client_phone || <span style={{ color: '#475569' }}>—</span>}</TD>

                  {/* 4. Amount */}
                  <TD style={{ color: '#f8fafc', fontWeight: '600' }}>{formatCurrency(inv.amount)}</TD>

                  {/* 5. Due Date */}
                  <TD>{formatDate(inv.due_date)}</TD>

                  {/* 6. Days Passed */}
                  <TD>
                    {inv.days_passed > 0 ? (
                      <span style={{ color: inv.days_passed > 30 ? '#ef4444' : '#f59e0b', fontWeight: '600' }}>
                        {inv.days_passed}d
                      </span>
                    ) : (
                      <span style={{ color: '#10b981' }}>Not due</span>
                    )}
                  </TD>

                  {/* 7. Last Contacted */}
                  <TD>{formatDate(inv.last_contacted)}</TD>

                  {/* 8. Paused Until */}
                  <TD>
                    {isPausedActive ? (
                      <span style={{
                        color: '#60a5fa',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}>
                        {formatDate(inv.pause_followups_until)}
                      </span>
                    ) : (
                      <span style={{ color: '#475569' }}>—</span>
                    )}
                  </TD>

                  {/* Status */}
                  <TD>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        display: 'inline-block',
                        backgroundColor: statusStyle.bg,
                        color: statusStyle.text,
                        padding: '2px 8px',
                        borderRadius: '9999px',
                        fontSize: '11px',
                        fontWeight: '600'
                      }}>
                        {inv.status}
                      </span>
                      {inv.status !== 'PAID' && (
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              handleWriteOff(inv.id, e.target.value);
                              e.target.value = '';
                            }
                          }}
                          disabled={isActing}
                          style={{
                            background: 'transparent',
                            border: '1px solid rgba(255,255,255,0.2)',
                            color: '#cbd5e1',
                            borderRadius: '4px',
                            fontSize: '10px',
                            padding: '2px 4px',
                            cursor: isActing ? 'not-allowed' : 'pointer'
                          }}
                        >
                          <option value="" style={{ color: '#000' }}>Update...</option>
                          {inv.status !== 'OVERDUE' && <option value="OVERDUE" style={{ color: '#000' }}>Revert to Overdue</option>}
                          {inv.status !== 'BAD_DEBT' && <option value="BAD_DEBT" style={{ color: '#000' }}>Bad Debt</option>}
                          {inv.status !== 'LEGAL' && <option value="LEGAL" style={{ color: '#000' }}>Legal</option>}
                        </select>
                      )}
                    </div>
                  </TD>

                  {/* 9. Razorpay Link */}
                  <TD>
                    {inv.razorpay_short_url ? (
                      <a
                        href={inv.razorpay_short_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: '#3b82f6', textDecoration: 'none', fontSize: '13px' }}
                      >
                        View ↗
                      </a>
                    ) : (
                      <span style={{ color: '#475569' }}>None</span>
                    )}
                  </TD>

                  {/* 10. Requires Call */}
                  <TD>
                    {inv.requires_call ? (
                      <span style={{
                        backgroundColor: 'rgba(239, 68, 68, 0.15)',
                        color: '#ef4444',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '700',
                        display: 'inline-block'
                      }}>
                        ⚠️ Call
                      </span>
                    ) : (
                      <span style={{ color: '#475569' }}>—</span>
                    )}
                  </TD>

                  {/* 11. Actions */}
                  <TD>
                    {inv.status !== 'PAID' ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '150px' }}>
                        {/* Negotiate Date UI */}
                        {negotiatingDateFor === inv.id ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <input
                              type="date"
                              value={proposedDate}
                              onChange={(e) => setProposedDate(e.target.value)}
                              min={new Date().toISOString().split('T')[0]} // prevent past dates on frontend
                              style={{
                                padding: '4px 6px',
                                borderRadius: '4px',
                                border: '1px solid rgba(255,255,255,0.2)',
                                background: 'rgba(0,0,0,0.3)',
                                color: '#f8fafc',
                                fontSize: '12px',
                                colorScheme: 'dark'
                              }}
                            />
                            <div style={{ display: 'flex', gap: '4px' }}>
                              <button
                                onClick={() => handleSaveDate(inv.id)}
                                disabled={isActing}
                                style={{ flex: 1, padding: '4px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: '600' }}
                              >
                                {isActing ? '...' : 'Save'}
                              </button>
                              <button
                                onClick={() => { setNegotiatingDateFor(null); setProposedDate(''); }}
                                disabled={isActing}
                                style={{ flex: 1, padding: '4px', background: '#475569', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: '600' }}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <div style={{ display: 'flex', gap: '6px' }}>
                              <button
                                onClick={() => { setNegotiatingDateFor(inv.id); setProposedDate(inv.pause_followups_until || ''); }}
                                disabled={isActing}
                                style={{
                                  flex: 1,
                                  background: 'transparent',
                                  border: '1px solid #a855f7',
                                  color: '#a855f7',
                                  padding: '6px 8px',
                                  borderRadius: '6px',
                                  cursor: isActing ? 'not-allowed' : 'pointer',
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  transition: 'all 0.2s'
                                }}
                                onMouseOver={e => { if (!isActing) { e.target.style.background = '#a855f7'; e.target.style.color = '#fff'; } }}
                                onMouseOut={e => { if (!isActing) { e.target.style.background = 'transparent'; e.target.style.color = '#a855f7'; } }}
                              >
                                Negotiate Date
                              </button>

                              <button
                                onClick={() => handleResendLink(inv.id)}
                                disabled={isActing || recentlySent === inv.id}
                                style={{
                                  flex: 1,
                                  background: (isActing || recentlySent === inv.id) ? 'rgba(59,130,246,0.2)' : 'transparent',
                                  border: '1px solid #3b82f6',
                                  color: (recentlySent === inv.id) ? '#60a5fa' : '#3b82f6',
                                  padding: '6px 8px',
                                  borderRadius: '6px',
                                  cursor: (isActing || recentlySent === inv.id) ? 'not-allowed' : 'pointer',
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  transition: 'all 0.2s'
                                }}
                                onMouseOver={e => { if (!isActing && recentlySent !== inv.id) { e.target.style.background = '#3b82f6'; e.target.style.color = '#fff'; } }}
                                onMouseOut={e => { if (!isActing && recentlySent !== inv.id) { e.target.style.background = 'transparent'; e.target.style.color = '#3b82f6'; } }}
                              >
                                {isActing && actingOn === inv.id && recentlySent !== inv.id ? '...' : (recentlySent === inv.id ? 'Sent ✓' : 'Resend Link')}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: '#475569', fontSize: '13px' }}>No actions (Paid)</span>
                    )}
                  </TD>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
