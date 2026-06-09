import { CameraView, useCameraPermissions, type BarcodeScanningResult } from "expo-camera";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

type MobileQrScannerProps = {
  onClose: () => void;
  onScan: (payload: string) => void;
};

export function MobileQrScanner({ onClose, onScan }: MobileQrScannerProps) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanLocked, setScanLocked] = useState(false);

  const handleBarcodeScanned = (result: BarcodeScanningResult) => {
    if (scanLocked || !result.data) {
      return;
    }

    setScanLocked(true);
    onScan(result.data);
  };

  if (!permission) {
    return (
      <View style={styles.panel}>
        <Text style={styles.title}>Camera Scanner</Text>
        <View style={styles.centeredState}>
          <ActivityIndicator color="#38bdf8" />
          <Text style={styles.helperText}>Checking camera permissions.</Text>
        </View>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.panel}>
        <Text style={styles.title}>Camera Scanner</Text>
        <Text style={styles.helperText}>
          Allow camera access to scan a gateway or tag QR code directly from the mobile workflow.
        </Text>
        <View style={styles.buttonRow}>
          <Pressable onPress={() => void requestPermission()} style={styles.primaryButton}>
            <Text style={styles.primaryButtonLabel}>Allow Camera</Text>
          </Pressable>
          <Pressable onPress={onClose} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonLabel}>Use Manual Entry</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.panel}>
      <View style={styles.headerRow}>
        <View style={styles.headerCopy}>
          <Text style={styles.title}>Camera Scanner</Text>
          <Text style={styles.helperText}>
            Point the camera at a QR code. Scanning pauses after the first read so you can confirm
            the resolved target.
          </Text>
        </View>
        <Pressable onPress={onClose} style={styles.closeButton}>
          <Text style={styles.closeButtonLabel}>Close</Text>
        </Pressable>
      </View>
      <View style={styles.cameraFrame}>
        <CameraView
          barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
          onBarcodeScanned={handleBarcodeScanned}
          style={styles.camera}
        />
        <View pointerEvents="none" style={styles.overlay}>
          <View style={styles.scanWindow} />
        </View>
      </View>
      <View style={styles.footerRow}>
        <Text style={styles.helperText}>
          {scanLocked
            ? "Scan captured. Review the resolved device below or close the scanner to scan again."
            : "Camera-first scanning is the primary path; manual entry remains available for simulators."}
        </Text>
        {scanLocked ? (
          <Pressable
            onPress={() => setScanLocked(false)}
            style={[styles.secondaryButton, styles.footerButton]}
          >
            <Text style={styles.secondaryButtonLabel}>Scan Again</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: "#08101e",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#1f3a56",
    padding: 14,
    gap: 12
  },
  headerRow: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
    justifyContent: "space-between"
  },
  headerCopy: {
    flex: 1,
    gap: 6
  },
  title: {
    color: "#f8fafc",
    fontSize: 18,
    fontWeight: "700"
  },
  helperText: {
    color: "#94a3b8",
    fontSize: 13,
    lineHeight: 19
  },
  centeredState: {
    minHeight: 120,
    alignItems: "center",
    justifyContent: "center",
    gap: 10
  },
  buttonRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  primaryButton: {
    backgroundColor: "#0284c7",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 14
  },
  primaryButtonLabel: {
    color: "#f8fafc",
    fontSize: 14,
    fontWeight: "700"
  },
  secondaryButton: {
    backgroundColor: "#0f172a",
    borderWidth: 1,
    borderColor: "#334155",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 14
  },
  secondaryButtonLabel: {
    color: "#e2e8f0",
    fontSize: 14,
    fontWeight: "700"
  },
  closeButton: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: "#0f172a",
    borderWidth: 1,
    borderColor: "#334155"
  },
  closeButtonLabel: {
    color: "#e2e8f0",
    fontSize: 13,
    fontWeight: "700"
  },
  cameraFrame: {
    overflow: "hidden",
    borderRadius: 18,
    aspectRatio: 1,
    minHeight: 260,
    backgroundColor: "#020617"
  },
  camera: {
    flex: 1
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(2, 6, 23, 0.22)"
  },
  scanWindow: {
    width: "72%",
    aspectRatio: 1,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: "#38bdf8",
    backgroundColor: "rgba(14, 165, 233, 0.08)"
  },
  footerRow: {
    gap: 12
  },
  footerButton: {
    alignSelf: "flex-start"
  }
});
