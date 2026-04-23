import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import Plot from "react-plotly.js";
import "./App.css";

const API_ROOT =
  import.meta.env.VITE_ML_API_BASE_URL ||
  `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8081"}/api/ml`;
const INTEGRATION_API_ROOT =
  import.meta.env.VITE_INTEGRATION_API_BASE_URL ||
  `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8081"}/api/integration`;
const DEFAULT_TENANT_ID = import.meta.env.VITE_TENANT_ID || "demo-tenant";
const DEFAULT_USER_ID = import.meta.env.VITE_USER_ID || "demo-user";
const DEFAULT_USER_ROLES = import.meta.env.VITE_USER_ROLES || "ROLE_ADMIN";

const TABS = [
  { id: "overview", label: "Vue d'ensemble" },
  { id: "simulator", label: "Simulateur" },
  { id: "alerts", label: "Alertes & Décisions" },
  { id: "performance", label: "Performances Modèles" },
  { id: "models", label: "Gestion Modèles" }
];

const TEAM = [
  { nom: "LOMOFOUET NDONGMO", role: "Chercheur en IA", photo: "photo1.jpg", init: "N1" },
  { nom: "NANGO IDRISS", role: "Chercheur en IA", photo: "photo2.jpg", init: "N2" },
  { nom: "KEMADJEU NGOUNOU", role: "Chercheur en IA", photo: "photo3.jpg", init: "N3" },
  { nom: "DONGMO ARNOLD", role: "Chercheur en IA", photo: "photo4.jpeg", init: "N4" },
  { nom: "NGUIMDO KENFACK", role: "Chercheur en IA", photo: "photo5.jpg", init: "N5" },
  { nom: "KAMGAD ZUKAM", role: "Chercheur en IA", photo: "photo6.jpg", init: "N6" },
  { nom: "FOSSO TIOFOUET", role: "Chercheur en IA", photo: "photo7.jpg", init: "N7" },
  { nom: "KALZIBE DOMINIQUE", role: "Chercheur en RSD", photo: "photo8.jpg", init: "N8" },
  { nom: "PEUHT AOGNEBE", role: "Chercheur en RSD", photo: "photo9.jpg", init: "N9" },
  { nom: "NGO KANDA", role: "Chercheur en RSD", photo: "photo10.jpg", init: "N10" },
  { nom: "YUMKAM SIMO", role: "Chercheur en RSD", photo: "photo11.jpg", init: "N11" },
  { nom: "NONA FOGHAP", role: "Chercheur en RSD", photo: "photo12.jpg", init: "N12" }
];

const PLOT_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Outfit, sans-serif", color: "#2C1810" },
  colorway: ["#2D6A2E", "#E8820C", "#8B5E3C", "#2980B9", "#4CAF50", "#F5A623"],
  margin: { l: 60, r: 30, t: 60, b: 50 }
};

const ALERT_DEFAULTS = {
  rain_variation_pct: -20,
  temp_variation_c: 1.5,
  pesticides_variation_pct: 0
};

function plotLayout(title, height = 380) {
  return {
    ...PLOT_LAYOUT,
    height,
    title: { text: title, font: { family: "Source Serif 4, serif", size: 16, color: "#1B4332" } }
  };
}

function fmt(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return Number(value).toLocaleString("fr-FR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
}

function shortModelVersion(modelVersion) {
  if (!modelVersion) {
    return "-";
  }
  if (modelVersion.length <= 20) {
    return modelVersion;
  }
  return `${modelVersion.slice(0, 16)}...${modelVersion.slice(-6)}`;
}

function modelDisplayName(entry) {
  if (!entry) {
    return "-";
  }
  const name = String(entry.display_name || "").trim();
  return name || shortModelVersion(entry.model_version);
}

function extractErrorMessage(err, fallback) {
  return err?.response?.data?.message || err?.response?.data?.detail || err?.message || fallback;
}

function formatFreshness(seconds) {
  const safe = Number.isFinite(Number(seconds)) ? Math.max(0, Number(seconds)) : 0;
  if (safe < 60) {
    return `${safe}s`;
  }
  if (safe < 3600) {
    return `${Math.floor(safe / 60)} min`;
  }
  return `${Math.floor(safe / 3600)} h`;
}

export default function App() {
  const [tenantId] = useState(DEFAULT_TENANT_ID);
  const [userId] = useState(DEFAULT_USER_ID);
  const [userRoles] = useState(
    DEFAULT_USER_ROLES.split(",")
      .map((role) => role.trim())
      .filter(Boolean)
  );

  const isAdmin = userRoles.includes("ROLE_ADMIN");
  const isAnalyst = isAdmin || userRoles.includes("ROLE_ANALYST");
  const canUploadDataset = isAnalyst;
  const canManageModels = isAdmin;

  const [activeTab, setActiveTab] = useState("overview");
  const [uploading, setUploading] = useState(false);
  const [globalLoading, setGlobalLoading] = useState(false);
  const [error, setError] = useState("");

  const [datasetLoaded, setDatasetLoaded] = useState(false);
  const [training, setTraining] = useState(null);
  const [overview, setOverview] = useState(null);
  const [performance, setPerformance] = useState(null);

  const [countries, setCountries] = useState([]);
  const [modelRegistry, setModelRegistry] = useState(null);
  const [fineTuneResult, setFineTuneResult] = useState(null);
  const [selectedModelVersion, setSelectedModelVersion] = useState("");
  const [modelActionLoading, setModelActionLoading] = useState(false);
  const [modelNameDrafts, setModelNameDrafts] = useState({});

  const [simCountry, setSimCountry] = useState("");
  const [simCrop, setSimCrop] = useState("");
  const [simCrops, setSimCrops] = useState([]);
  const [simContext, setSimContext] = useState(null);
  const [simForm, setSimForm] = useState({
    target_year: 0,
    rain_variation_pct: 0,
    temp_variation_c: 0,
    pesticides_variation_pct: 0
  });
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  const [alertCountry, setAlertCountry] = useState("");
  const [alertCrop, setAlertCrop] = useState("");
  const [alertCrops, setAlertCrops] = useState([]);
  const [alertForm, setAlertForm] = useState(ALERT_DEFAULTS);
  const [alertResult, setAlertResult] = useState(null);
  const [alertLoading, setAlertLoading] = useState(false);
  const [trustSignal, setTrustSignal] = useState(null);
  const [trustSignalLoading, setTrustSignalLoading] = useState(false);

  const [stateChecked, setStateChecked] = useState(false);
  const simRequestRef = useRef(0);
  const alertRequestRef = useRef(0);
  const availableTabs = useMemo(
    () =>
      TABS.filter((tab) => {
        if (tab.id === "models") {
          return isAdmin;
        }
        if (tab.id === "performance") {
          return isAnalyst;
        }
        return true;
      }),
    [isAdmin, isAnalyst]
  );
  const trustSelection = useMemo(() => {
    if (activeTab === "alerts" && alertCountry && alertCrop) {
      return { country: alertCountry, crop: alertCrop };
    }
    if (simCountry && simCrop) {
      return { country: simCountry, crop: simCrop };
    }
    if (countries[0]) {
      return { country: countries[0], crop: "" };
    }
    return { country: "", crop: "" };
  }, [activeTab, alertCountry, alertCrop, simCountry, simCrop, countries]);

  useEffect(() => {
    axios.defaults.headers.common["X-Tenant-Id"] = tenantId;
    axios.defaults.headers.common["X-User-Id"] = userId;
    axios.defaults.headers.common["X-User-Roles"] = userRoles.join(",");
    delete axios.defaults.headers.common.Authorization;
    void bootstrapFromServer();
  }, [tenantId, userId, userRoles]);

  useEffect(() => {
    if (!availableTabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(availableTabs[0]?.id || "overview");
    }
  }, [availableTabs, activeTab]);

  useEffect(() => {
    if (!datasetLoaded || !trustSelection.country || !trustSelection.crop) {
      setTrustSignal(null);
      return;
    }
    void loadTrustSignal(trustSelection.country, trustSelection.crop);
  }, [datasetLoaded, trustSelection.country, trustSelection.crop]);

  useEffect(() => {
    if (!datasetLoaded || !simCountry) {
      return;
    }
    void loadSimCrops(simCountry);
  }, [datasetLoaded, simCountry]);

  useEffect(() => {
    if (!datasetLoaded || !simCountry || !simCrop) {
      return;
    }
    setSimContext(null);
    setSimResult(null);
    void loadScenarioContext(simCountry, simCrop);
  }, [datasetLoaded, simCountry, simCrop]);

  useEffect(() => {
    if (!datasetLoaded || !alertCountry) {
      return;
    }
    void loadAlertCrops(alertCountry);
  }, [datasetLoaded, alertCountry]);

  useEffect(() => {
    if (!datasetLoaded || !alertCountry || !alertCrop) {
      return;
    }
    setAlertForm({ ...ALERT_DEFAULTS });
    setAlertResult(null);
  }, [datasetLoaded, alertCountry, alertCrop]);

  useEffect(() => {
    if (
      !datasetLoaded ||
      !simCountry ||
      !simCrop ||
      !simContext ||
      simContext.country !== simCountry ||
      simContext.crop !== simCrop
    ) {
      return;
    }
    const timeout = setTimeout(() => {
      void runSimulation(simCountry, simCrop, simForm);
    }, 260);
    return () => clearTimeout(timeout);
  }, [
    datasetLoaded,
    simCountry,
    simCrop,
    simContext,
    simForm.target_year,
    simForm.rain_variation_pct,
    simForm.temp_variation_c,
    simForm.pesticides_variation_pct
  ]);

  useEffect(() => {
    if (!datasetLoaded || !alertCountry || !alertCrop) {
      return;
    }
    const timeout = setTimeout(() => {
      void runAlerts(alertCountry, alertCrop, alertForm);
    }, 260);
    return () => clearTimeout(timeout);
  }, [
    datasetLoaded,
    alertCountry,
    alertCrop,
    alertForm.rain_variation_pct,
    alertForm.temp_variation_c,
    alertForm.pesticides_variation_pct
  ]);

  async function bootstrapFromServer() {
    setError("");
    try {
      const response = await axios.get(`${API_ROOT}/state`);
      if (response.data?.ready) {
        await loadDashboardData(response.data);
      }
    } catch {
      // Backend not ready yet, keep hero page.
    } finally {
      setStateChecked(true);
    }
  }

  function normalizeTraining(payload) {
    if (!payload) {
      return null;
    }
    if (payload.best_model) {
      return payload;
    }
    if (payload.model) {
      return {
        best_model: payload.model,
        r2: payload.r2,
        samples: payload.samples,
        year_min: payload.year_min,
        year_max: payload.year_max,
        dataset_hash: payload.dataset_hash,
        dataset_source: payload.dataset_source || payload.source
      };
    }
    return null;
  }

  async function loadDashboardData(trainingHint = null) {
    setGlobalLoading(true);
    setError("");
    try {
      const [overviewRes, countriesRes, performanceRes, registryRes] = await Promise.all([
        axios.get(`${API_ROOT}/overview`),
        axios.get(`${API_ROOT}/options/countries`),
        axios.get(`${API_ROOT}/performance`),
        axios.get(`${API_ROOT}/model/registry`)
      ]);

      setOverview(overviewRes.data);
      setPerformance(performanceRes.data);

      const normalized = normalizeTraining(trainingHint) || normalizeTraining(overviewRes.data?.training);
      setTraining(normalized);

      const registry = registryRes.data || null;
      setModelRegistry(registry);
      const versionList = registry?.versions || [];
      setSelectedModelVersion((prev) => {
        if (prev && versionList.some((row) => row.model_version === prev)) {
          return prev;
        }
        return registry?.active_model_version || "";
      });
      setModelNameDrafts((prev) => {
        const nextDrafts = {};
        versionList.forEach((row) => {
          const currentName = String(row.display_name || row.model_version || "").trim();
          nextDrafts[row.model_version] = prev[row.model_version] ?? currentName;
        });
        return nextDrafts;
      });

      const countryList = countriesRes.data?.countries || [];
      setCountries(countryList);
      setDatasetLoaded(countryList.length > 0);

      if (countryList.length > 0) {
        setSimCountry((prev) => (countryList.includes(prev) ? prev : countryList[0]));
        setAlertCountry((prev) => (countryList.includes(prev) ? prev : countryList[0]));
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de charger le dashboard"));
      setDatasetLoaded(false);
    } finally {
      setGlobalLoading(false);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await axios.post(`${API_ROOT}/train/upload`, formData, {
        params: {
          mode: "finetune",
          promote_if_better: false,
          replace_dataset: true
        },
        headers: { "Content-Type": "multipart/form-data" }
      });
      setFineTuneResult(response.data || null);
      await loadDashboardData(response.data);
      setActiveTab("overview");
    } catch (err) {
      setError(extractErrorMessage(err, "Échec du chargement du CSV"));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function loadSimCrops(country) {
    try {
      const response = await axios.get(`${API_ROOT}/options/crops`, { params: { country } });
      const cropList = response.data?.crops || [];
      setSimCrops(cropList);
      setSimCrop((prev) => (cropList.includes(prev) ? prev : cropList[0] || ""));
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de charger les cultures (simulateur)"));
    }
  }

  async function loadAlertCrops(country) {
    try {
      const response = await axios.get(`${API_ROOT}/options/crops`, { params: { country } });
      const cropList = response.data?.crops || [];
      setAlertCrops(cropList);
      setAlertCrop((prev) => (cropList.includes(prev) ? prev : cropList[0] || ""));
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de charger les cultures (alertes)"));
    }
  }

  async function loadTrustSignal(country, crop) {
    setTrustSignalLoading(true);
    try {
      const response = await axios.get(`${INTEGRATION_API_ROOT}/signals/realtime`, {
        params: { country, crop }
      });
      setTrustSignal(response.data || null);
    } catch {
      setTrustSignal(null);
    } finally {
      setTrustSignalLoading(false);
    }
  }

  async function loadScenarioContext(country, crop) {
    try {
      const response = await axios.get(`${API_ROOT}/scenario/context`, {
        params: { country, crop }
      });
      const context = response.data;
      setSimContext(context);

      const targetYear = Math.min((context.latest_year || 0) + 1, 2050);
      const defaultPayload = {
        target_year: targetYear,
        rain_variation_pct: 0,
        temp_variation_c: 0,
        pesticides_variation_pct: 0
      };
      setSimForm(defaultPayload);
    } catch (err) {
      setSimContext(null);
      setSimResult(null);
      setError(extractErrorMessage(err, "Impossible de charger le contexte de simulation"));
    }
  }

  async function runSimulation(country, crop, payload) {
    const requestId = ++simRequestRef.current;
    setSimLoading(true);
    setError("");
    try {
      const response = await axios.post(`${API_ROOT}/scenario/simulate`, {
        country,
        crop,
        ...payload
      });
      if (requestId !== simRequestRef.current) {
        return;
      }
      setSimResult(response.data);
    } catch (err) {
      if (requestId !== simRequestRef.current) {
        return;
      }
      setError(extractErrorMessage(err, "Échec de la simulation"));
      setSimResult(null);
    } finally {
      if (requestId === simRequestRef.current) {
        setSimLoading(false);
      }
    }
  }

  async function runAlerts(country, crop, payload) {
    const requestId = ++alertRequestRef.current;
    setAlertLoading(true);
    setError("");
    try {
      const response = await axios.post(`${API_ROOT}/alerts`, {
        country,
        crop,
        ...payload
      });
      if (requestId !== alertRequestRef.current) {
        return;
      }
      setAlertResult(response.data);
    } catch (err) {
      if (requestId !== alertRequestRef.current) {
        return;
      }
      setError(extractErrorMessage(err, "Échec de la génération d'alertes"));
      setAlertResult(null);
    } finally {
      if (requestId === alertRequestRef.current) {
        setAlertLoading(false);
      }
    }
  }

  async function activateModelVersion(modelVersion) {
    if (!modelVersion) {
      return;
    }
    setModelActionLoading(true);
    setError("");
    try {
      await axios.post(`${API_ROOT}/model/activate`, {
        model_version: modelVersion
      });
      setFineTuneResult(null);
      await loadDashboardData();
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible d'activer ce modèle"));
    } finally {
      setModelActionLoading(false);
    }
  }

  async function revertToBaseline() {
    setModelActionLoading(true);
    setError("");
    try {
      await axios.post(`${API_ROOT}/model/revert-baseline`);
      setFineTuneResult(null);
      await loadDashboardData();
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de revenir au modèle de base"));
    } finally {
      setModelActionLoading(false);
    }
  }

  function keepCurrentModel() {
    setFineTuneResult(null);
  }

  async function renameModelVersion(modelVersion) {
    const nextName = String(modelNameDrafts[modelVersion] || "").trim();
    if (!nextName) {
      setError("Le nom du modèle ne peut pas être vide");
      return;
    }

    setModelActionLoading(true);
    setError("");
    try {
      await axios.patch(`${API_ROOT}/model/${encodeURIComponent(modelVersion)}/name`, {
        display_name: nextName
      });
      await loadDashboardData();
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de renommer ce modèle"));
    } finally {
      setModelActionLoading(false);
    }
  }

  async function deleteModelVersion(modelVersion) {
    if (!window.confirm("Supprimer ce modèle ? Cette action est irréversible.")) {
      return;
    }

    setModelActionLoading(true);
    setError("");
    try {
      await axios.delete(`${API_ROOT}/model/${encodeURIComponent(modelVersion)}`);
      setFineTuneResult(null);
      await loadDashboardData();
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de supprimer ce modèle"));
    } finally {
      setModelActionLoading(false);
    }
  }

  const fineTuneRecommendation = useMemo(() => {
    if (!fineTuneResult?.candidate) {
      return null;
    }
    const candidateR2 = Number(fineTuneResult.candidate?.r2 ?? Number.NEGATIVE_INFINITY);
    const activeR2 = Number(training?.r2 ?? Number.NEGATIVE_INFINITY);
    const useCandidate = candidateR2 >= activeR2;

    return {
      recommendedModelVersion: useCandidate
        ? fineTuneResult.candidate.model_version
        : modelRegistry?.active_model_version,
      message: useCandidate
        ? "Le modèle fine-tuné est recommandé (R² supérieur ou égal)."
        : "Le modèle actif reste recommandé (R² supérieur)."
    };
  }, [fineTuneResult, training, modelRegistry]);

  const sensitivityTraces = useMemo(() => {
    if (!simResult?.sensitivity) {
      return [];
    }
    const colors = {
      Précipitations: "#2980B9",
      Intrants: "#4CAF50",
      Température: "#E8820C"
    };

    const grouped = simResult.sensitivity.reduce((acc, row) => {
      if (!acc[row.variable]) {
        acc[row.variable] = [];
      }
      acc[row.variable].push(row);
      return acc;
    }, {});

    return Object.entries(grouped).map(([variable, values]) => {
      const ordered = [...values].sort((a, b) => a.variation_pct - b.variation_pct);
      return {
        type: "scatter",
        mode: "lines+markers",
        name: variable,
        x: ordered.map((item) => item.variation_pct),
        y: ordered.map((item) => item.yield),
        line: { color: colors[variable] || "#2D6A2E" },
        marker: { size: 6 }
      };
    });
  }, [simResult]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo-wrap">
          <img src="/logo.png" alt="AgriYield" className="sidebar-logo" />
        </div>
        <h2>Chargement des données</h2>
        <hr />
        <label className={`upload-zone ${!canUploadDataset ? "disabled" : ""}`}>
          <span>
            {uploading
              ? "Chargement en cours..."
              : canUploadDataset
                ? "Importer yield_df.csv"
                : "Import réservé admin/analyste"}
          </span>
          <input
            type="file"
            accept=".csv"
            onChange={handleUpload}
            disabled={uploading || !canUploadDataset}
          />
        </label>
        <hr />
        <p className="sidebar-source">Données sources : FAO / Kaggle</p>

        {datasetLoaded && training && (
          <>
            <div className="card card-orange sidebar-model-card">
              <div className="card-header">
                <span className="icon">military_tech</span> Modèle actif
              </div>
              <div className="card-value small">{training.best_model}</div>
              <div className="card-footer">Précision (R²) : {fmt(training.r2, 4)}</div>
              <div className="card-footer">Nom : {training.display_name || shortModelVersion(training.model_version)}</div>
              <div className="card-footer">Version : {shortModelVersion(training.model_version)}</div>
            </div>

            <div className="trust-panel">
              <div className="trust-panel-title">
                <span className="icon">verified_user</span> Confiance Décision
              </div>
              <div className="trust-panel-line">
                <span>Tenant</span>
                <strong>{tenantId}</strong>
              </div>
              <div className="trust-panel-line">
                <span>Utilisateur</span>
                <strong>{userId}</strong>
              </div>
              <div className="trust-panel-line">
                <span>Rôles</span>
                <strong>{userRoles.join(", ") || "-"}</strong>
              </div>
              <div className="trust-panel-line">
                <span>Version modèle</span>
                <code>{shortModelVersion(training.model_version)}</code>
              </div>
              <div className="trust-panel-line">
                <span>Couverture temporelle</span>
                <strong>{`${training.year_min || "-"} - ${training.year_max || "-"}`}</strong>
              </div>
              <div className="trust-panel-line">
                <span>Source dataset</span>
                <strong>{training.dataset_source || training.source || "-"}</strong>
              </div>
              <div className="trust-panel-line">
                <span>Hash dataset</span>
                <code>{shortModelVersion(training.dataset_hash)}</code>
              </div>
              <div className="trust-panel-line">
                <span>Évaluation</span>
                <strong>{training.evaluation_strategy || "-"}</strong>
              </div>

              <div className="trust-signal-head">
                <span>Signaux externes</span>
                <strong>
                  {trustSignalLoading
                    ? "chargement..."
                    : trustSignal
                      ? `fraîcheur ${formatFreshness(trustSignal.signalFreshnessSeconds)}`
                      : "indisponible"}
                </strong>
              </div>
              <div
                className={`trust-signal-status ${
                  !trustSignal || trustSignal.degraded ? "degraded" : "healthy"
                }`}
              >
                {!trustSignal ? "Signal indisponible" : trustSignal.degraded ? "Mode dégradé" : "Mode nominal"}
                {trustSignal?.confidence !== undefined ? ` • confiance ${fmt(trustSignal.confidence, 2)}` : ""}
              </div>
              {trustSignal?.sources && (
                <div className="trust-sources">
                  {Object.entries(trustSignal.sources).map(([key, value]) => (
                    <div key={key} className="trust-source-item">
                      <span>{key}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>
              )}
              {trustSignal?.warnings?.length > 0 && (
                <div className="trust-warnings">
                  {trustSignal.warnings.slice(0, 2).map((warning, index) => (
                    <div key={`${warning}-${index}`} className="trust-warning-item">
                      {warning}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {modelRegistry && (
              <div className="model-governance">
                <div className="model-governance-title">
                  <span className="icon">tune</span> Gouvernance Modèle
                </div>
                <div className="model-governance-line">
                  Base : {shortModelVersion(modelRegistry.baseline_model_version)}
                </div>
                <div className="model-governance-line">
                  Recommandé global : {shortModelVersion(modelRegistry.recommended_model_version)}
                </div>

                {fineTuneResult?.candidate && (
                  <div className="fine-tune-summary">
                    <div className="fine-tune-title">Résultat Fine-tuning</div>
                    <div className="fine-tune-row">Actif R² : {fmt(training.r2, 4)}</div>
                    <div className="fine-tune-row">Candidat R² : {fmt(fineTuneResult.candidate.r2, 4)}</div>
                    <div className="fine-tune-recommendation">{fineTuneRecommendation?.message}</div>
                    {canManageModels ? (
                      <div className="model-actions-row">
                        <button
                          type="button"
                          className="primary-btn mini"
                          disabled={modelActionLoading || !fineTuneRecommendation?.recommendedModelVersion}
                          onClick={() => activateModelVersion(fineTuneRecommendation?.recommendedModelVersion)}
                        >
                          {modelActionLoading ? "Application..." : "Appliquer recommandé"}
                        </button>
                        <button type="button" className="ghost-btn" onClick={keepCurrentModel} disabled={modelActionLoading}>
                          Garder l'actif
                        </button>
                      </div>
                    ) : (
                      <div className="model-readonly-note">Activation réservée au rôle admin.</div>
                    )}
                  </div>
                )}

                <label className="field-wrap model-field-wrap">
                  <span>Choisir un modèle enregistré</span>
                  <select
                    value={selectedModelVersion}
                    onChange={(event) => setSelectedModelVersion(event.target.value)}
                    disabled={!canManageModels}
                  >
                    {(modelRegistry.versions || []).map((entry) => (
                      <option key={entry.model_version} value={entry.model_version}>
                        {`${modelDisplayName(entry)} | ${entry.mode} | R² ${fmt(entry.r2, 4)}`}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="model-actions-row">
                  <button
                    type="button"
                    className="secondary-btn mini"
                    disabled={modelActionLoading || !selectedModelVersion || !canManageModels}
                    onClick={() => activateModelVersion(selectedModelVersion)}
                  >
                    {modelActionLoading ? "Activation..." : "Activer ce modèle"}
                  </button>
                  <button
                    type="button"
                    className="danger-btn"
                    disabled={modelActionLoading || !modelRegistry.baseline_model_version || !canManageModels}
                    onClick={revertToBaseline}
                  >
                    Revenir au modèle de base
                  </button>
                </div>
                {!canManageModels && (
                  <div className="model-readonly-note">Mode lecture seule pour ce rôle.</div>
                )}
              </div>
            )}
          </>
        )}
      </aside>

      <main className="main-content">
        <header className="navbar">
          <div className="navbar-brand">
            <div className="navbar-logo icon">spa</div>
            <div>
              <div className="navbar-title">AgriYield</div>
              <div className="navbar-subtitle">Système de Prédiction et d'Aide à la Décision</div>
            </div>
          </div>
          <div className="navbar-badge">La technologie au service de la résilience agricole.</div>
        </header>

        {error && <div className="global-error">{error}</div>}

        {!datasetLoaded && stateChecked && (
          <>
            <section className="hero" style={{ backgroundImage: "linear-gradient(rgba(27,67,50,0.8), rgba(45,106,46,0.7)), url('/Img1.jpg')" }}>
              <span className="hero-icon icon">grass</span>
              <h1>Plateforme AgriYield</h1>
              <p>
                Solution analytique avancée pour la prédiction des rendements agricoles. Simulez des scénarios de contraintes
                climatiques, paramétrez vos intrants et optimisez vos stratégies de sécurité alimentaire via nos modèles
                d'Intelligence Artificielle.
              </p>
            </section>

            <div className="feature-grid">
              <FeatureCard icon="query_stats" title="Analyse Historique" />
              <FeatureCard icon="science" title="Modélisation & Simulation" />
              <FeatureCard icon="notifications_active" title="Système d'Alerte" />
              <FeatureCard icon="account_tree" title="Aide à la Décision" />
            </div>

            <p className="inject-hint">
              Veuillez injecter le fichier source <strong>yield_df.csv</strong>
            </p>
          </>
        )}

        {datasetLoaded && (
          <>
            <div className="tabs">
              {availableTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {globalLoading ? (
              <div className="panel-loading">Chargement du tableau de bord...</div>
            ) : (
              <>
                {activeTab === "overview" && overview && (
                  <section>
                    <h3 className="section-title">
                      <span className="icon">dashboard</span> Aperçu des données historiques
                    </h3>

                    <div className="metric-grid four">
                      <MetricCard label="Observations" value={fmt(overview.metrics?.observations)} accent="green" />
                      <MetricCard label="Pays" value={fmt(overview.metrics?.countries)} accent="orange" />
                      <MetricCard label="Cultures" value={fmt(overview.metrics?.crops)} accent="brown" />
                      <MetricCard
                        label="Période"
                        value={`${overview.metrics?.year_min || "-"} – ${overview.metrics?.year_max || "-"}`}
                        accent="blue"
                      />
                    </div>

                    <div className="plot-grid two">
                      <div className="plot-card">
                        <Plot
                          data={[
                            {
                              type: "scatter",
                              mode: "lines",
                              x: (overview.trend || []).map((row) => row.year),
                              y: (overview.trend || []).map((row) => row.yield),
                              fill: "tozeroy",
                              line: { color: "#2D6A2E" },
                              fillcolor: "rgba(45,106,46,0.12)",
                              name: "Rendement"
                            }
                          ]}
                          layout={plotLayout("Évolution globale du rendement", 380)}
                          config={{ displayModeBar: false, responsive: true }}
                          style={{ width: "100%" }}
                        />
                      </div>

                      <div className="plot-card">
                        <Plot
                          data={[
                            {
                              type: "bar",
                              orientation: "h",
                              y: (overview.yield_by_crop || []).map((row) => row.crop),
                              x: (overview.yield_by_crop || []).map((row) => row.yield),
                              marker: {
                                color: (overview.yield_by_crop || []).map((row) => row.yield),
                                colorscale: [
                                  [0, "#E8F5E9"],
                                  [0.25, "#A5D6A7"],
                                  [0.5, "#66BB6A"],
                                  [0.75, "#2E7D32"],
                                  [1, "#1B4332"]
                                ]
                              },
                              name: "Rendement"
                            }
                          ]}
                          layout={plotLayout("Rendement par culture", 380)}
                          config={{ displayModeBar: false, responsive: true }}
                          style={{ width: "100%" }}
                        />
                      </div>
                    </div>
                  </section>
                )}

                {activeTab === "simulator" && (
                  <section>
                    <h3 className="section-title">
                      <span className="icon">science</span> Simulateur de scénarios climatiques
                    </h3>
                    <p className="section-subtext">
                      Ajustez les variables environnementales pour anticiper l'impact sur la production agricole.
                    </p>
                    <div className="live-row">
                      <span className={`live-chip ${simLoading ? "is-loading" : "is-ready"}`}>
                        <span className="icon">{simLoading ? "autorenew" : "bolt"}</span>
                        {simLoading ? "Recalcul en cours..." : "Recalcul automatique actif"}
                      </span>
                      <span className="live-meta">
                        Les résultats se mettent à jour dès que vous modifiez les curseurs.
                      </span>
                    </div>

                    <div className="controls-grid two">
                      <SelectField label="Pays ciblé" value={simCountry} onChange={setSimCountry} options={countries} />
                      <SelectField label="Type de culture" value={simCrop} onChange={setSimCrop} options={simCrops} />
                    </div>

                    {simContext && (
                      <>
                        <div className="controls-grid year-grid">
                          <label className="field-wrap">
                            <span>Année de projection</span>
                            <input
                              type="number"
                              min={simContext.latest_year}
                              max={2050}
                              step={1}
                              value={simForm.target_year}
                              onChange={(event) =>
                                setSimForm((prev) => ({ ...prev, target_year: Number(event.target.value) }))
                              }
                            />
                          </label>
                          <div className="info-box">
                            La dernière année de données réelles pour <strong>{simCrop}</strong> au <strong>{simCountry}</strong> est <strong>{simContext.latest_year}</strong>.
                          </div>
                        </div>

                        <div className="controls-grid three scenario-sliders">
                          <SliderField
                            title={`Précipitations — Base: ${fmt(simContext.rain_base)} mm`}
                            min={-50}
                            max={50}
                            step={5}
                            value={simForm.rain_variation_pct}
                            unit="%"
                            onChange={(value) => setSimForm((prev) => ({ ...prev, rain_variation_pct: value }))}
                            caption={`→ ${fmt(simContext.rain_base * (1 + simForm.rain_variation_pct / 100))} mm/an`}
                          />
                          <SliderField
                            title={`Température — Base: ${fmt(simContext.temp_base, 1)} °C`}
                            min={-5}
                            max={5}
                            step={0.5}
                            value={simForm.temp_variation_c}
                            unit="°C"
                            onChange={(value) => setSimForm((prev) => ({ ...prev, temp_variation_c: value }))}
                            caption={`→ ${fmt(simContext.temp_base + simForm.temp_variation_c, 1)} °C`}
                          />
                          <SliderField
                            title={`Produits phytosanitaires — Base: ${fmt(simContext.pesticides_base)} t`}
                            min={-50}
                            max={100}
                            step={5}
                            value={simForm.pesticides_variation_pct}
                            unit="%"
                            onChange={(value) => setSimForm((prev) => ({ ...prev, pesticides_variation_pct: value }))}
                            caption={`→ ${fmt(simContext.pesticides_base * (1 + simForm.pesticides_variation_pct / 100))} tonnes`}
                          />
                        </div>

                        <button
                          type="button"
                          className="secondary-btn"
                          onClick={() => runSimulation(simCountry, simCrop, simForm)}
                          disabled={simLoading}
                        >
                          {simLoading ? "Simulation en cours..." : "Recalculer maintenant (optionnel)"}
                        </button>
                      </>
                    )}

                    {simResult && (
                      <>
                        <div className="metric-grid four">
                          <MetricCard
                            label="Moy. Historique"
                            value={fmt(simResult.metrics?.historical_mean)}
                            accent="brown"
                            footer="hg/ha"
                          />
                          <MetricCard
                            label={`Base (${simResult.context?.target_year})`}
                            value={fmt(simResult.metrics?.base_prediction)}
                            accent="green"
                            footer="hg/ha"
                          />
                          <MetricCard
                            label={`Scénario (${simResult.context?.target_year})`}
                            value={fmt(simResult.metrics?.scenario_prediction)}
                            accent={simResult.metrics?.variation_pct >= 0 ? "green" : "orange"}
                            footer={`${simResult.metrics?.variation_pct >= 0 ? "▲" : "▼"} ${fmt(simResult.metrics?.variation_pct, 1)}%`}
                          />
                          <MetricCard
                            label="Différentiel net"
                            value={`${simResult.metrics?.delta >= 0 ? "+" : ""}${fmt(simResult.metrics?.delta)}`}
                            accent="blue"
                            footer="hg/ha"
                          />
                        </div>

                        <hr className="separator" />
                        
                        <div className="plot-card">
                          <Plot
                            data={[
                              {
                                type: "bar",
                                x: ["Rendement", "Rendement", "Rendement"],
                                y: (simResult.comparison || []).map((item) => item.value),
                                text: (simResult.comparison || []).map((item) => fmt(item.value)),
                                textposition: "outside",
                                marker: { color: (simResult.comparison || []).map((item) => item.color) },
                                name: "Comparaison"
                              }
                            ]}
                            layout={{
                              ...plotLayout(
                                `Analyse comparative — ${simCrop || "Culture"} dans ${simCountry || "Pays"}`,
                                400
                              ),
                              barmode: "group"
                            }}
                            config={{ displayModeBar: false, responsive: true }}
                            style={{ width: "100%" }}
                          />
                        </div>

                        <h3 className="section-title">
                          <span className="icon">multiline_chart</span> Analyse de sensibilité
                        </h3>
                        <div className="plot-card">
                          <Plot
                            data={sensitivityTraces}
                            layout={{
                              ...plotLayout("Sensibilité du rendement face à l'isolation des variables", 400),
                              shapes: [
                                {
                                  type: "line",
                                  x0: -40,
                                  x1: 45,
                                  y0: simResult.metrics?.base_prediction,
                                  y1: simResult.metrics?.base_prediction,
                                  line: { color: "#8B5E3C", dash: "dash" }
                                }
                              ]
                            }}
                            config={{ displayModeBar: false, responsive: true }}
                            style={{ width: "100%" }}
                          />
                        </div>

                        <h3 className="section-title">
                          <span className="icon">assignment</span> Scénarios de stress prédéfinis
                        </h3>
                        <div className="table-wrap">
                          <table className="stress-table">
                            <thead>
                              <tr>
                                <th>Scénario de Test</th>
                                <th>Rendement ({simResult.context?.target_year})</th>
                                <th>Variation</th>
                                <th>État</th>
                              </tr>
                            </thead>
                            <tbody>
                              {(simResult.stress || []).map((row) => (
                                <tr key={row.scenario}>
                                  <td>{row.scenario}</td>
                                  <td>{fmt(row.yield)}</td>
                                  <td>{`${row.variation_pct >= 0 ? "+" : ""}${fmt(row.variation_pct, 1)}%`}</td>
                                  <td>{row.state}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    )}
                  </section>
                )}

                {activeTab === "alerts" && (
                  <section>
                    <h3 className="section-title">
                      <span className="icon">campaign</span> Alertes
                    </h3>
                    <div className="live-row">
                      <span className={`live-chip ${alertLoading ? "is-loading" : "is-ready"}`}>
                        <span className="icon">{alertLoading ? "autorenew" : "bolt"}</span>
                        {alertLoading ? "Analyse en cours..." : "Analyse automatique active"}
                      </span>
                      <span className="live-meta">
                        Les alertes et recommandations se recalculent automatiquement quand les curseurs changent.
                      </span>
                    </div>

                    <div className="controls-grid two">
                      <SelectField label="Pays ciblé" value={alertCountry} onChange={setAlertCountry} options={countries} />
                      <SelectField label="Culture ciblée" value={alertCrop} onChange={setAlertCrop} options={alertCrops} />
                    </div>

                    <div className="controls-grid three scenario-sliders">
                      <SliderField
                        title="Pluie (%)"
                        min={-50}
                        max={50}
                        step={5}
                        value={alertForm.rain_variation_pct}
                        unit="%"
                        onChange={(value) => setAlertForm((prev) => ({ ...prev, rain_variation_pct: value }))}
                      />
                      <SliderField
                        title="Temp (°C)"
                        min={-5}
                        max={5}
                        step={0.5}
                        value={alertForm.temp_variation_c}
                        unit="°C"
                        onChange={(value) => setAlertForm((prev) => ({ ...prev, temp_variation_c: value }))}
                      />
                      <SliderField
                        title="Pesticides (%)"
                        min={-50}
                        max={100}
                        step={5}
                        value={alertForm.pesticides_variation_pct}
                        unit="%"
                        onChange={(value) => setAlertForm((prev) => ({ ...prev, pesticides_variation_pct: value }))}
                      />
                    </div>

                    <button
                      type="button"
                      className="secondary-btn"
                      disabled={alertLoading}
                      onClick={() => runAlerts(alertCountry, alertCrop, alertForm)}
                    >
                      {alertLoading ? "Analyse en cours..." : "Recalculer maintenant (optionnel)"}
                    </button>

                    {alertResult && (
                      <>
                        <hr className="separator" />
                        <div className="metric-grid four">
                          <MetricCard label="Historique" value={fmt(alertResult.stats?.rend_historique)} accent="brown" footer="hg/ha" />
                          <MetricCard label="Projection de base" value={fmt(alertResult.stats?.pred_base)} accent="green" footer="hg/ha" />
                          <MetricCard
                            label="Projection scénarisée"
                            value={fmt(alertResult.stats?.pred_modifie)}
                            accent={alertResult.stats?.variation_pct >= 0 ? "green" : "orange"}
                            footer="hg/ha"
                          />
                          <MetricCard
                            label="Variation attendue"
                            value={`${alertResult.stats?.variation_pct >= 0 ? "+" : ""}${fmt(alertResult.stats?.variation_pct, 1)}%`}
                            accent={alertResult.stats?.variation_pct >= 0 ? "blue" : "orange"}
                          />
                        </div>
                        <div>
                          {(alertResult.alerts || []).map((alert, index) => (
                            <AlertCard key={`${alert.type}-${index}`} alert={alert} />
                          ))}
                          {(alertResult.recommendations || []).map((reco, index) => (
                            <RecommendationPanel key={index} recommendation={reco} />
                          ))}
                        </div>
                        <hr className="separator" />
                      </>
                    )}
                  </section>
                )}


                {activeTab === "models" && modelRegistry && (
                  <section>
                    <h3 className="section-title">
                      <span className="icon">inventory_2</span> Catalogue des modèles
                    </h3>
                    <p className="section-subtext">Renommez, activez ou supprimez les modèles. Le modèle de base reste protégé.</p>

                    <div className="table-wrap model-table-wrap">
                      <table className="stress-table model-table">
                        <thead>
                          <tr>
                            <th>Nom</th>
                            <th>Version</th>
                            <th>Mode</th>
                            <th>R²</th>
                            <th>Statut</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(modelRegistry.versions || []).map((entry) => {
                            const isActive = entry.model_version === modelRegistry.active_model_version;
                            const isBaseline = entry.model_version === modelRegistry.baseline_model_version;
                            const isRecommended = entry.model_version === modelRegistry.recommended_model_version;
                            const draftName = modelNameDrafts[entry.model_version] ?? modelDisplayName(entry);

                            return (
                              <tr key={entry.model_version}>
                                <td>
                                  <input
                                    className="model-name-input"
                                    type="text"
                                    maxLength={80}
                                    value={draftName}
                                    onChange={(event) =>
                                      setModelNameDrafts((prev) => ({
                                        ...prev,
                                        [entry.model_version]: event.target.value
                                      }))
                                    }
                                  />
                                </td>
                                <td>
                                  <code>{shortModelVersion(entry.model_version)}</code>
                                </td>
                                <td>{entry.mode}</td>
                                <td>{fmt(entry.r2, 4)}</td>
                                <td>
                                  <div className="model-badges">
                                    {isActive && <span className="model-badge active">Actif</span>}
                                    {isBaseline && <span className="model-badge baseline">Base</span>}
                                    {isRecommended && <span className="model-badge recommended">Recommandé</span>}
                                  </div>
                                </td>
                                <td>
                                  <div className="model-actions-row">
                                    <button
                                      type="button"
                                      className="secondary-btn mini"
                                      disabled={modelActionLoading || isActive}
                                      onClick={() => activateModelVersion(entry.model_version)}
                                    >
                                      {isActive ? "Actif" : "Activer"}
                                    </button>
                                    <button
                                      type="button"
                                      className="primary-btn mini"
                                      disabled={modelActionLoading || !String(draftName || "").trim()}
                                      onClick={() => renameModelVersion(entry.model_version)}
                                    >
                                      Renommer
                                    </button>
                                    <button
                                      type="button"
                                      className="danger-btn"
                                      disabled={modelActionLoading || isBaseline}
                                      onClick={() => deleteModelVersion(entry.model_version)}
                                    >
                                      Supprimer
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </section>
                )}

                {activeTab === "performance" && performance && (
                  <section>
                    <h3 className="section-title">
                      <span className="icon">model_training</span> Performances
                    </h3>

                    <div className="plot-card">
                      <Plot
                        data={[
                          {
                            type: "bar",
                            orientation: "h",
                            x: (performance.feature_importance || []).map((item) => item.importance),
                            y: (performance.feature_importance || []).map((item) => item.feature),
                            marker: {
                              color: (performance.feature_importance || []).map((item) => item.importance),
                              colorscale: [
                                [0, "#E8F5E9"],
                                [0.25, "#A5D6A7"],
                                [0.5, "#66BB6A"],
                                [0.75, "#2E7D32"],
                                [1, "#1B4332"]
                              ]
                            }
                          }
                        ]}
                        layout={plotLayout(`Poids des Variables — ${performance.best_model}`, 360)}
                        config={{ displayModeBar: false, responsive: true }}
                        style={{ width: "100%" }}
                      />
                    </div>
                  </section>
                )}
              </>
            )}
          </>
        )}

        <footer className="footer">
          <div className="footer-title">
            <span className="icon">spa</span> AgriYield
          </div>
          <div>Solution d'Aide à la Décision Agronomique | Architecture propulsée par le Machine Learning</div>
          <div className="footer-team-title">
            <strong>Développé par l'équipe 12 chercheurs en IA et RSD :</strong>
          </div>
          <div className="dev-grid">
            {TEAM.map((dev) => (
              <DevCard key={dev.nom} dev={dev} />
            ))}
          </div>
        </footer>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title }) {
  return (
    <div className="feature-card">
      <div className="feature-icon icon">{icon}</div>
      <div className="feature-title">{title}</div>
    </div>
  );
}

function MetricCard({ label, value, accent = "green", footer = "" }) {
  return (
    <div className={`card card-${accent}`}>
      <div className="card-header">{label}</div>
      <div className="card-value">{value}</div>
      {footer ? <div className="card-footer">{footer}</div> : null}
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="field-wrap">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {(options || []).map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function SliderField({ title, min, max, step, value, onChange, caption, unit = "" }) {
  const progress = max === min ? 0 : ((value - min) / (max - min)) * 100;
  const valueLabel = `${value > 0 ? "+" : ""}${value}${unit}`;
  return (
    <div className="slider-wrap">
      <p className="slider-title">{title}</p>
      <input
        className="slider-range"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        style={{ "--range-progress": `${Math.min(100, Math.max(0, progress))}%` }}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <div className={`slider-value ${value < 0 ? "negative" : "positive"}`}>{valueLabel}</div>
      {caption ? <p className="slider-caption">{caption}</p> : null}
    </div>
  );
}

function AlertCard({ alert }) {
  return (
    <div className={`alert alert-${alert.type}`}>
      <div className="alert-title" dangerouslySetInnerHTML={{ __html: alert.title }} />
      <div className="alert-body">{alert.message}</div>
    </div>
  );
}

function RecommendationPanel({ recommendation }) {
  return (
    <div className="reco-panel">
      <div className="reco-panel-header" dangerouslySetInnerHTML={{ __html: recommendation.category }} />
      <div className="reco-panel-body">
        {(recommendation.actions || []).map((action, index) => (
          <div key={`${action}-${index}`} className="reco-item">
            <div className="reco-bullet">{index + 1}</div>
            <div className="reco-text">{action}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DevCard({ dev }) {
  const [broken, setBroken] = useState(false);

  return (
    <div className="dev-card">
      {!broken ? (
        <img
          src={`/${dev.photo}`}
          alt={dev.nom}
          className="dev-avatar"
          onError={() => setBroken(true)}
        />
      ) : (
        <div className="dev-avatar avatar-fallback">{dev.init}</div>
      )}
      <div className="dev-details">
        <span className="dev-name">{dev.nom}</span>
        <span className="dev-info">{dev.role}</span>
      </div>
    </div>
  );
}
