import { StatusBar } from "expo-status-bar";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function App() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <View style={styles.panel}>
        <Text style={styles.eyebrow}>Mobile Baseline</Text>
        <Text style={styles.title}>RTLS Analytics Platform</Text>
        <Text style={styles.body}>
          Expo React Native is the new mobile baseline for asset finding and administrator
          workflows.
        </Text>
        <Text style={styles.meta}>API target: {apiBaseUrl}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#08101e"
  },
  panel: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 48,
    justifyContent: "center",
    backgroundColor: "#0f172a"
  },
  eyebrow: {
    color: "#22d3ee",
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 12
  },
  title: {
    color: "#f8fafc",
    fontSize: 34,
    fontWeight: "700",
    marginBottom: 16
  },
  body: {
    color: "#cbd5e1",
    fontSize: 17,
    lineHeight: 26,
    marginBottom: 16
  },
  meta: {
    color: "#67e8f9",
    fontSize: 14
  }
});
