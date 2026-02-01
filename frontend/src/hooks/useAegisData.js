/**
 * Custom hook for fetching and managing CIC data
 */

import { useState, useEffect, useCallback } from "react";
import * as api from "../api/client";

export function useAegisData(pollInterval = 2000) {
  const [patients, setPatients] = useState([]);
  const [trackedPeople, setTrackedPeople] = useState([]);
  const [stats, setStats] = useState({
    total_tracked: 0,
    tagged_patients: 0,
    untagged: 0,
    staff_count: 0,
    critical_located: 0,
    urgent_located: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      const [patientsData, trackedData, statsData] = await Promise.all([
        api.getPatients(),
        api.getTracked(),
        api.getStats(),
      ]);

      // Transform tracked data to match frontend format
      const transformedTracked = trackedData.map((t) => ({
        track_id: t.track_id,
        patient_id: t.patient_id,
        position: t.map_position, // Use map_position for display
        person_type: t.person_type,
      }));

      setPatients(patientsData);
      setTrackedPeople(transformedTracked);
      setStats(statsData);
      setError(null);
      setIsConnected(true);
    } catch (err) {
      console.error("Failed to fetch data:", err);
      setError(err.message);
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch + polling
  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, pollInterval);
    return () => clearInterval(interval);
  }, [fetchData, pollInterval]);

  // Enroll patient
  const enroll = useCallback(async (trackId, patientId) => {
    try {
      await api.enrollPatient(trackId, patientId);
      await fetchData(); // Refresh data
      return true;
    } catch (err) {
      console.error("Enrollment failed:", err);
      return false;
    }
  }, [fetchData]);

  // Update vitals (demo)
  const updateVitals = useCallback(async (patientId, direction) => {
    try {
      await api.demoUpdateVitals(patientId, direction);
      await fetchData(); // Refresh data
      return true;
    } catch (err) {
      console.error("Vitals update failed:", err);
      return false;
    }
  }, [fetchData]);

  // Demo: Add person
  const addPerson = useCallback(async (cameraId, personType) => {
    try {
      await api.demoAddPerson(cameraId, personType);
      await fetchData();
      return true;
    } catch (err) {
      console.error("Add person failed:", err);
      return false;
    }
  }, [fetchData]);

  // Demo: Setup
  const setupDemo = useCallback(async () => {
    try {
      await api.demoSetup();
      await fetchData();
      return true;
    } catch (err) {
      console.error("Demo setup failed:", err);
      return false;
    }
  }, [fetchData]);

  // Demo: Clear
  const clearAll = useCallback(async () => {
    try {
      await api.demoClear();
      await fetchData();
      return true;
    } catch (err) {
      console.error("Clear failed:", err);
      return false;
    }
  }, [fetchData]);

  return {
    // Data
    patients,
    trackedPeople,
    stats,

    // State
    loading,
    error,
    isConnected,

    // Actions
    enroll,
    updateVitals,
    addPerson,
    setupDemo,
    clearAll,
    refresh: fetchData,
  };
}
