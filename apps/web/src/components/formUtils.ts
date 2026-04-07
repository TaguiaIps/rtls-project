import { useCallback, useState } from "react";

/**
 * Technical validation hook for real-time ID and formatting checks.
 */
export function useTechnicalValidation() {
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const validateTagId = useCallback((id: string) => {
    if (!id) return "Tag ID is required";
    if (!/^[A-Z0-9_-]{3,20}$/i.test(id)) {
      return "Tag ID must be 3-20 alphanumeric characters (plus - or _)";
    }
    return null;
  }, []);

  const validateMacAddress = useCallback((mac: string) => {
    if (!mac) return "MAC address is required";
    if (!/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/.test(mac)) {
      return "Invalid MAC address format (e.g., AA:BB:CC:DD:EE:FF)";
    }
    return null;
  }, []);

  const validateIpAddress = useCallback((ip: string) => {
    if (!ip) return "IP address is required";
    if (!/^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(ip)) {
      return "Invalid IP address format (e.g., 192.168.1.1)";
    }
    return null;
  }, []);

  const clearError = useCallback((field: string) => {
    setErrors((prev) => ({ ...prev, [field]: null }));
  }, []);

  const setError = useCallback((field: string, message: string) => {
    setErrors((prev) => ({ ...prev, [field]: message }));
  }, []);

  return {
    errors,
    validateTagId,
    validateMacAddress,
    validateIpAddress,
    clearError,
    setError
  };
}

/**
 * Utility functions for input masks.
 */
export const inputMasks = {
  macAddress: (value: string) => {
    const hex = value.replace(/[^0-9A-Fa-f]/g, "").toUpperCase();
    const parts = hex.match(/.{1,2}/g) || [];
    return parts.slice(0, 6).join(":");
  },
  ipAddress: (value: string) => {
    return value.replace(/[^0-9.]/g, "").replace(/\.{2,}/g, ".");
  }
};
