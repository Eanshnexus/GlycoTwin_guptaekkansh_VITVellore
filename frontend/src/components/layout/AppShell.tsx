import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export interface AppShellProps {
  currentPatientId?: string;
  selectedPatientId?: string;
  onSelectPatient: (patientId: string) => void;
  children?: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentPatientId,
  selectedPatientId,
  onSelectPatient,
  children,
}) => {
  const activeId = selectedPatientId || currentPatientId || 'HUPA0001P';

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar
          selectedPatientId={activeId}
          onSelectPatient={onSelectPatient}
        />

        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
};

export default AppShell;
