import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  Pressable
} from "react-native";

import { AssetFinderScreen } from "./src/AssetFinderScreen";
import { CommissioningScreen } from "./src/CommissioningScreen";

const defaultApiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const defaultWebBaseUrl = process.env.EXPO_PUBLIC_WEB_BASE_URL ?? "http://localhost:5173";

type MobileMode = "finder" | "commissioning";

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(defaultApiBaseUrl);
  const [webBaseUrl, setWebBaseUrl] = useState(defaultWebBaseUrl);
  const [accessToken, setAccessToken] = useState("");
  const [mode, setMode] = useState<MobileMode>("finder");

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.headerCard}>
          <Text style={styles.headerEyebrow}>RTLS Analytics Platform</Text>
          <Text style={styles.headerTitle}>Mobile Operations Workspace</Text>
          <Text style={styles.headerBody}>
            Keep the delivered Asset Finder available for Carlos and add a mobile commissioning
            workflow for Alex without leaving the Expo baseline.
          </Text>
        </View>

        <View style={styles.panel}>
          <Text style={styles.panelTitle}>Mobile Session</Text>
          <Text style={styles.helperText}>
            Dedicated mobile sign-in is still deferred. Paste a current access token and adjust
            the API or web targets when testing against a different local environment.
          </Text>

          <Text style={styles.fieldLabel}>API base URL</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setApiBaseUrl}
            placeholder="http://localhost:8000"
            placeholderTextColor="#64748b"
            style={styles.input}
            value={apiBaseUrl}
          />

          <Text style={styles.fieldLabel}>Web base URL</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setWebBaseUrl}
            placeholder="http://localhost:5173"
            placeholderTextColor="#64748b"
            style={styles.input}
            value={webBaseUrl}
          />

          <Text style={styles.fieldLabel}>Access token</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setAccessToken}
            placeholder="Paste a valid Bearer token"
            placeholderTextColor="#64748b"
            secureTextEntry
            style={[styles.input, styles.tokenInput]}
            value={accessToken}
          />
        </View>

        <View style={styles.modeRail}>
          <Pressable
            onPress={() => setMode("finder")}
            style={({ pressed }) => [
              styles.modeButton,
              mode === "finder" && styles.modeButtonActive,
              pressed ? styles.modeButtonPressed : null
            ]}
          >
            <Text style={styles.modeLabel}>Finder</Text>
          </Pressable>
          <Pressable
            onPress={() => setMode("commissioning")}
            style={({ pressed }) => [
              styles.modeButton,
              mode === "commissioning" && styles.modeButtonActive,
              pressed ? styles.modeButtonPressed : null
            ]}
          >
            <Text style={styles.modeLabel}>Commissioning</Text>
          </Pressable>
        </View>

        {mode === "finder" ? (
          <AssetFinderScreen
            accessToken={accessToken}
            apiBaseUrl={apiBaseUrl}
            webBaseUrl={webBaseUrl}
          />
        ) : (
          <CommissioningScreen accessToken={accessToken} apiBaseUrl={apiBaseUrl} />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#08101e"
  },
  scrollContent: {
    paddingHorizontal: 18,
    paddingVertical: 20,
    gap: 16
  },
  headerCard: {
    backgroundColor: "#0f172a",
    borderRadius: 24,
    paddingHorizontal: 20,
    paddingVertical: 22,
    borderWidth: 1,
    borderColor: "#163047"
  },
  headerEyebrow: {
    color: "#38bdf8",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 10
  },
  headerTitle: {
    color: "#f8fafc",
    fontSize: 30,
    fontWeight: "700",
    lineHeight: 36,
    marginBottom: 12
  },
  headerBody: {
    color: "#cbd5e1",
    fontSize: 16,
    lineHeight: 24
  },
  panel: {
    backgroundColor: "#0f172a",
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 18,
    borderWidth: 1,
    borderColor: "#1e293b",
    gap: 10
  },
  panelTitle: {
    color: "#f8fafc",
    fontSize: 20,
    fontWeight: "700"
  },
  helperText: {
    color: "#94a3b8",
    fontSize: 14,
    lineHeight: 20
  },
  fieldLabel: {
    color: "#cbd5e1",
    fontSize: 13,
    fontWeight: "600",
    marginTop: 4
  },
  input: {
    backgroundColor: "#08101e",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#233248",
    color: "#f8fafc",
    fontSize: 15,
    paddingHorizontal: 14,
    paddingVertical: 12
  },
  tokenInput: {
    minHeight: 54
  },
  modeRail: {
    flexDirection: "row",
    gap: 10
  },
  modeButton: {
    flex: 1,
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: "center",
    backgroundColor: "#122234",
    borderWidth: 1,
    borderColor: "#20324a"
  },
  modeButtonActive: {
    backgroundColor: "#113149",
    borderColor: "#38bdf8"
  },
  modeButtonPressed: {
    opacity: 0.92
  },
  modeLabel: {
    color: "#f8fafc",
    fontSize: 15,
    fontWeight: "700"
  }
});
