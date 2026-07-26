import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Tabs } from '../../ui/tabs';
import AuditLogTab from './AuditLogTab';
import EmailLogsTab from './EmailLogsTab';

describe('admin log tabs', () => {
  it('displays each email delivery status without rewriting it', () => {
    const emailLogs = ['sent', 'failed', 'bounced'].map((status, index) => ({
      id: index + 1,
      sent_at: '2026-07-16T10:00:00Z',
      recipient_name: 'Candidate',
      recipient_email: `candidate${index}@example.com`,
      email_type: 'assessment_invitation',
      subject: 'Your assessment',
      status,
    }));

    render(
      <Tabs value="email-logs">
        <EmailLogsTab emailLogs={emailLogs} />
      </Tabs>,
    );

    expect(screen.getByText('sent')).toBeInTheDocument();
    expect(screen.getByText('failed')).toBeInTheDocument();
    expect(screen.getByText('bounced')).toBeInTheDocument();
    expect(screen.queryByText('completed')).not.toBeInTheDocument();
  });

  it('describes only the actions captured by the audit endpoint', () => {
    render(
      <Tabs value="audit-log">
        <AuditLogTab auditLogs={[]} />
      </Tabs>,
    );

    expect(screen.getByText('Review recorded role, sector, and candidate-matching actions.')).toBeInTheDocument();
  });
});
