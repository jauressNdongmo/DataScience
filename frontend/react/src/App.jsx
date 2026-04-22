import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import Plot from "react-plotly.js";
import "./App.css";

const API_ROOT =
  import.meta.env.VITE_ML_API_BASE_URL ||
  `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8081"}/api/ml`;

const TABS = [
  { id: "overview", label: "Vue d'ensemble" },
  { id: "simulator", label: "Simulateur" },
  { id: "alerts", label: "Alertes & Décisions" },
  { id: "performance", label: "Performances Modèles" }
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

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [uploading, setUploading] = useState(false);
  const [globalLoading, setGlobalLoading] = useState(false);
  const [error, setError] = useState("");

  const [datasetLoaded, setDatasetLoaded] = useState(false);
  const [training, setTraining] = useState(null);
  const [overview, setOverview] = useState(null);
  const [performance, setPerformance] = useState(null);

  const [countries, setCountries] = useState([]);

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

  const [stateChecked, setStateChecked] = useState(false);

  useEffect(() => {
    void bootstrapFromServer();
  }, []);

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
    void runAlerts(alertCountry, alertCrop, ALERT_DEFAULTS);
    setAlertForm(ALERT_DEFAULTS);
  }, [datasetLoaded, alertCountry, alertCrop]);

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
        samples: payload.samples
      };
    }
    return null;
  }

  async function loadDashboardData(trainingHint = null) {
    setGlobalLoading(true);
    setError("");
    try {
      const [overviewRes, countriesRes, performanceRes] = await Promise.all([
        axios.get(`${API_ROOT}/overview`),
        axios.get(`${API_ROOT}/options/countries`),
        axios.get(`${API_ROOT}/performance`)
      ]);

      setOverview(overviewRes.data);
      setPerformance(performanceRes.data);

      const normalized = normalizeTraining(trainingHint) || normalizeTraining(overviewRes.data?.training);
      setTraining(normalized);

      const countryList = countriesRes.data?.countries || [];
      setCountries(countryList);
      setDatasetLoaded(countryList.length > 0);

      if (countryList.length > 0) {
        setSimCountry((prev) => (countryList.includes(prev) ? prev : countryList[0]));
        setAlertCountry((prev) => (countryList.includes(prev) ? prev : countryList[0]));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Impossible de charger le dashboard");
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
        headers: { "Content-Type": "multipart/form-data" }
      });
      await loadDashboardData(response.data);
      setActiveTab("overview");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Échec du chargement du CSV");
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
      setError(err?.response?.data?.detail || err?.message || "Impossible de charger les cultures (simulateur)");
    }
  }

  async function loadAlertCrops(country) {
    try {
      const response = await axios.get(`${API_ROOT}/options/crops`, { params: { country } });
      const cropList = response.data?.crops || [];
      setAlertCrops(cropList);
      setAlertCrop((prev) => (cropList.includes(prev) ? prev : cropList[0] || ""));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Impossible de charger les cultures (alertes)");
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
      await runSimulation(country, crop, defaultPayload);
    } catch (err) {
      setSimContext(null);
      setSimResult(null);
      setError(err?.response?.data?.detail || err?.message || "Impossible de charger le contexte de simulation");
    }
  }

  async function runSimulation(country, crop, payload) {
    setSimLoading(true);
    setError("");
    try {
      const response = await axios.post(`${API_ROOT}/scenario/simulate`, {
        country,
        crop,
        ...payload
      });
      setSimResult(response.data);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Échec de la simulation");
      setSimResult(null);
    } finally {
      setSimLoading(false);
    }
  }

  async function runAlerts(country, crop, payload) {
    setAlertLoading(true);
    setError("");
    try {
      const response = await axios.post(`${API_ROOT}/alerts`, {
        country,
        crop,
        ...payload
      });
      setAlertResult(response.data);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Échec de la génération d'alertes");
      setAlertResult(null);
    } finally {
      setAlertLoading(false);
    }
  }

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
        <label className="upload-zone">
          <span>{uploading ? "Chargement en cours..." : "Importer yield_df.csv"}</span>
          <input type="file" accept=".csv" onChange={handleUpload} disabled={uploading} />
        </label>
        <hr />
        <p className="sidebar-source">Données sources : FAO / Kaggle</p>

        {datasetLoaded && training && (
          <div className="card card-orange sidebar-model-card">
            <div className="card-header">
              <span className="icon">military_tech</span> Meilleur modèle
            </div>
            <div className="card-value small">{training.best_model}</div>
            <div className="card-footer">Précision (R²) : {fmt(training.r2, 4)}</div>
          </div>
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
              {TABS.map((tab) => (
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

                        <div className="controls-grid three">
                          <SliderField
                            title={`Précipitations — Base: ${fmt(simContext.rain_base)} mm`}
                            min={-50}
                            max={50}
                            step={5}
                            value={simForm.rain_variation_pct}
                            onChange={(value) => setSimForm((prev) => ({ ...prev, rain_variation_pct: value }))}
                            caption={`→ ${fmt(simContext.rain_base * (1 + simForm.rain_variation_pct / 100))} mm/an`}
                          />
                          <SliderField
                            title={`Température — Base: ${fmt(simContext.temp_base, 1)} °C`}
                            min={-5}
                            max={5}
                            step={0.5}
                            value={simForm.temp_variation_c}
                            onChange={(value) => setSimForm((prev) => ({ ...prev, temp_variation_c: value }))}
                            caption={`→ ${fmt(simContext.temp_base + simForm.temp_variation_c, 1)} °C`}
                          />
                          <SliderField
                            title={`Produits phytosanitaires — Base: ${fmt(simContext.pesticides_base)} t`}
                            min={-50}
                            max={100}
                            step={5}
                            value={simForm.pesticides_variation_pct}
                            onChange={(value) => setSimForm((prev) => ({ ...prev, pesticides_variation_pct: value }))}
                            caption={`→ ${fmt(simContext.pesticides_base * (1 + simForm.pesticides_variation_pct / 100))} tonnes`}
                          />
                        </div>

                        <button
                          type="button"
                          className="primary-btn"
                          onClick={() => runSimulation(simCountry, simCrop, simForm)}
                          disabled={simLoading}
                        >
                          {simLoading ? "Simulation en cours..." : "Mettre à jour la simulation"}
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

                    <div className="controls-grid two">
                      <SelectField label="Pays ciblé" value={alertCountry} onChange={setAlertCountry} options={countries} />
                      <SelectField label="Culture ciblée" value={alertCrop} onChange={setAlertCrop} options={alertCrops} />
                    </div>

                    <div className="controls-grid three">
                      <SliderField
                        title="Pluie (%)"
                        min={-50}
                        max={50}
                        step={5}
                        value={alertForm.rain_variation_pct}
                        onChange={(value) => setAlertForm((prev) => ({ ...prev, rain_variation_pct: value }))}
                      />
                      <SliderField
                        title="Temp (°C)"
                        min={-5}
                        max={5}
                        step={0.5}
                        value={alertForm.temp_variation_c}
                        onChange={(value) => setAlertForm((prev) => ({ ...prev, temp_variation_c: value }))}
                      />
                      <SliderField
                        title="Pesticides (%)"
                        min={-50}
                        max={100}
                        step={5}
                        value={alertForm.pesticides_variation_pct}
                        onChange={(value) => setAlertForm((prev) => ({ ...prev, pesticides_variation_pct: value }))}
                      />
                    </div>

                    <button
                      type="button"
                      className="primary-btn"
                      disabled={alertLoading}
                      onClick={() => runAlerts(alertCountry, alertCrop, alertForm)}
                    >
                      {alertLoading ? "Génération en cours..." : "Actualiser alertes & décisions"}
                    </button>

                    {alertResult && (
                      <>
                        <hr className="separator" />
                        <div>
                          {(alertResult.alerts || []).map((alert, index) => (
                            <AlertCard key={`${alert.type}-${index}`} alert={alert} />
                          ))}
                          {(alertResult.recommendations || []).map((reco, index) => (
                            <RecommendationPanel key={index} recommendation={reco} />
                          ))}
                        </div>
                      </>
                    )}
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

function SliderField({ title, min, max, step, value, onChange, caption }) {
  return (
    <div className="slider-wrap">
      <p className="slider-title">{title}</p>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <div className="slider-value">{value}</div>
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
