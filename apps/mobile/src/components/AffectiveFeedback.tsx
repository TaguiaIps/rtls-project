import React, { useEffect } from "react";
import { StyleSheet, View, Text } from "react-native";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  Easing
} from "react-native-reanimated";

/**
 * HapticService utility for standard patterns.
 * Note: Real implementation would use expo-haptics.
 */
export const HapticService = {
  impact: () => {
    // In a real app: Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    console.log("[Haptics] Impact");
  },
  success: () => {
    // In a real app: Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    console.log("[Haptics] Success");
  }
};

export function CalibrationStepIndicator({
  current,
  total
}: {
  current: number;
  total: number;
}) {
  const steps = Array.from({ length: total }, (_, i) => i + 1);

  return (
    <View style={styles.container}>
      <View style={styles.track}>
        {steps.map((step) => (
          <View
            key={step}
            style={[
              styles.step,
              step < current && styles.stepComplete,
              step === current && styles.stepActive
            ]}
          />
        ))}
      </View>
      <Text style={styles.label}>
        STEP {current} OF {total}
      </Text>
    </View>
  );
}

export function IndustrialCompletionOverlay({ visible }: { visible: boolean }) {
  const scanlineY = useSharedValue(-100);

  useEffect(() => {
    if (visible) {
      scanlineY.value = withRepeat(
        withTiming(100, { duration: 1500, easing: Easing.bezier(0.4, 0, 0.2, 1) }),
        -1,
        false
      );
    }
  }, [visible, scanlineY]);

  const animatedStyle = useAnimatedStyle(() => ({
    top: `${scanlineY.value}%`
  }));

  if (!visible) return null;

  return (
    <View style={styles.overlay}>
      <Animated.View style={[styles.scanline, animatedStyle]} />
      <View style={styles.celebrationContent}>
        <Text style={styles.celebrationTitle}>BASELINE ESTABLISHED</Text>
        <Text style={styles.celebrationSubtitle}>Radiomap calibrated within 0.8m accuracy.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 16,
    gap: 8
  },
  track: {
    flexDirection: "row",
    gap: 4,
    height: 4
  },
  step: {
    flex: 1,
    backgroundColor: "#1e293b",
    borderRadius: 2
  },
  stepActive: {
    backgroundColor: "#0ea5e9",
    shadowColor: "#0ea5e9",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 4
  },
  stepComplete: {
    backgroundColor: "#38bdf8"
  },
  label: {
    fontFamily: "Space Grotesk", // Fallback to system if not loaded
    fontSize: 10,
    fontWeight: "700",
    color: "#94a3b8",
    letterSpacing: 1
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(14, 19, 30, 0.9)",
    zIndex: 100,
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden"
  },
  scanline: {
    position: "absolute",
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: "#00f0ff",
    shadowColor: "#00f0ff",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 10
  },
  celebrationContent: {
    alignItems: "center",
    gap: 12,
    padding: 24
  },
  celebrationTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#00f0ff",
    letterSpacing: 2,
    textAlign: "center"
  },
  celebrationSubtitle: {
    fontSize: 14,
    color: "#8ea2bc",
    textAlign: "center"
  }
});
