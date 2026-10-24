import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Overview } from './pages/Overview';
import { Patients } from './pages/Patients';
import { Predictions } from './pages/Predictions';
import { PersonalisationLab } from './pages/PersonalisationLab';
import { ModelEvaluation } from './pages/ModelEvaluation';
import { About } from './pages/About';
import './App.css';

export const App: React.FC = () => {
  // Global active patient selection, defaults to first clinical participant
  const [currentPatientId, setCurrentPatientId] = useState<string>('HUPA0001P');

  return (
    <BrowserRouter>
      <AppShell
        currentPatientId={currentPatientId}
        onSelectPatient={setCurrentPatientId}
      >
        <Routes>
          <Route 
            path="/" 
            element={
              <Overview 
                currentPatientId={currentPatientId} 
                onSelectPatient={setCurrentPatientId} 
              />
            } 
          />
          <Route 
            path="/patients" 
            element={
              <Patients 
                currentPatientId={currentPatientId} 
                onSelectPatient={setCurrentPatientId} 
              />
            } 
          />
          <Route 
            path="/patients/:patientId" 
            element={
              <Patients 
                currentPatientId={currentPatientId} 
                onSelectPatient={setCurrentPatientId} 
              />
            } 
          />
          <Route 
            path="/predictions" 
            element={
              <Predictions 
                currentPatientId={currentPatientId} 
              />
            } 
          />
          <Route 
            path="/personalisation" 
            element={
              <PersonalisationLab 
                currentPatientId={currentPatientId} 
                onSelectPatient={setCurrentPatientId} 
              />
            } 
          />
          <Route 
            path="/evaluation" 
            element={
              <ModelEvaluation />
            } 
          />
          <Route 
            path="/about" 
            element={
              <About />
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
};

export default App;
