# EpiSim — Disease Spread Simulation Platform

**EpiSim** is an academic-grade, interactive epidemic simulation platform built with Python and Streamlit. It implements compartmental mathematical models (SEIRD, SEIR, SIR, SIS) to simulate how infectious diseases spread through a population — and how public health interventions change that trajectory.

The platform is designed for students, researchers, and educators who want to explore epidemic dynamics, calibrate models to real outbreak data, and produce publication-quality visualisations — all without writing a single line of code.

---

## What the Platform Does

EpiSim solves a system of Ordinary Differential Equations (ODEs) that describe how individuals move between health states over time. Given a set of epidemiological parameters, it simulates the entire course of an outbreak — from the first infected individual to the final attack rate — and presents the results through a fully interactive dashboard.

### Supported Epidemic Models

| Model | Compartments | Best Used For |
|-------|-------------|---------------|
| **SEIRD** | S → E → I → R / D | COVID-19, Ebola — full dynamics with incubation and mortality |
| **SEIR** | S → E → I → R | Influenza — incubation period, no explicit mortality tracking |
| **SIR** | S → I → R | Simple outbreaks — Kermack–McKendrick classical model |
| **SIS** | S → I → S | Bacterial infections — no permanent immunity, endemic dynamics |

### Mathematical Basis (SEIRD)

$$\frac{dS}{dt} = -\beta \frac{SI}{N} \qquad \frac{dE}{dt} = \beta \frac{SI}{N} - \sigma E$$

$$\frac{dI}{dt} = \sigma E - (\gamma + \mu)I \qquad \frac{dR}{dt} = \gamma I \qquad \frac{dD}{dt} = \mu I$$

Where **β** is transmission rate, **σ** is incubation rate, **γ** is recovery rate, **μ** is case fatality rate, and **N** is the total population.

---

## How a User Works With EpiSim

### Step 1 — Choose a Model and Set Parameters

Open the **Simulation Controls** panel on the left side of the dashboard. Select an epidemic model architecture (SEIRD, SEIR, SIR, or SIS) and choose from built-in disease presets (COVID-19, Influenza, Ebola, Measles, SARS) or set parameters manually:

- **Population size (N)** — total people in the simulated community
- **Initial infected (I₀)** — number of infections at day 0
- **Transmission rate (β)** — how quickly the disease spreads between contacts
- **Incubation rate (σ)** — reciprocal of the mean incubation period in days
- **Recovery rate (γ)** — reciprocal of the mean infectious period in days
- **Case fatality rate (μ)** — fraction of infectious days ending in death
- **Vaccination coverage** — fraction immunised before the outbreak begins
- **Social distancing** — fractional reduction in effective transmission
- **Hospitalisation rate & ICU bed capacity** — for healthcare demand analysis

Every change instantly re-runs the simulation and updates all charts and metrics.

### Step 2 — Read the Simulation Dashboard (📈 Simulation Tab)

The main chart shows the full epidemic curve — an animated, day-by-day progression of all compartments (Susceptible, Exposed, Infectious, Recovered, Deaths). The animation can be played, paused, or scrubbed with a day slider.

Six academic metric cards display the most important summary statistics:

| Metric | Description |
|--------|-------------|
| **R₀** | Basic reproduction number — average secondary cases per infection |
| **Peak Active Infections** | Maximum simultaneously infectious individuals |
| **Peak Hospitalisations** | Peak hospital bed demand vs. ICU capacity |
| **Total Deaths** | Cumulative mortality with Case Fatality Ratio |
| **Herd Immunity Threshold** | Fraction of population that must be immune to stop spread (1 − 1/R₀) |
| **Doubling Time** | Initial exponential growth doubling time in days |

### Step 3 — Explore Advanced Analysis (🔬 Analysis Tab)

Four specialised scientific charts deepen the understanding of the epidemic:

- **Daily New Cases (Incidence Curve)** — bar chart of dI/dt per day, the standard epidemiological "wave" chart. Coloured bars highlight when daily cases exceed the 80th percentile.

- **Time-Varying Effective Reproduction Number Rt(t)** — shows how Rt falls from R₀ as the susceptible population depletes. A green dashed line at Rt = 1.0 marks the point of epidemic control. When Rt drops below 1, the epidemic enters exponential decline.

- **Phase Plane Portrait (S–I Trajectory)** — the classic mathematical epidemiology analysis tool. Plots the state-space trajectory of susceptibles vs. infectious individuals over time. The epidemic spirals from high-S/low-I toward the equilibrium. The vertical isocline where dI/dt = 0 (S = N/R₀) marks the exact epidemic peak.

- **Sensitivity / Tornado Analysis** — sweeps each parameter (β, σ, γ, μ, N, I₀) by ±20% and shows the resulting change in peak infections as a horizontal bar chart. The longest bars reveal which parameters have the greatest influence on the epidemic — the critical targets for intervention.

### Step 4 — Compare Scenarios (⚖️ Comparison Tab)

Without changing the left panel, navigate to the Comparison tab. The platform automatically runs a **baseline scenario** (no vaccination, no distancing) alongside the current intervention scenario and displays:

- **Overlay "flatten the curve" chart** — baseline (dashed red) vs. intervention (solid green) infectious curves on a single chart, with the ICU threshold shown
- **Rt(t) comparison** — side-by-side reproduction number trajectories showing how quickly the intervention brings Rt below 1
- **Impact headline** — lives saved and peak infections averted
- **Detailed breakdown table** — side-by-side comparison of all key metrics with change column

### Step 5 — Upload Real Data and Fit Parameters (📂 Dataset Upload Tab)

Upload any CSV file containing real epidemic outbreak data (e.g. WHO situation reports, national case counts) and the platform will:

1. **Preview the data** and let you map columns (Day, Active Cases, Deaths)
2. Offer two analysis modes:
   - **Auto-fit mode** — runs L-BFGS-B least-squares optimisation to find the β, σ, γ, μ values that best reproduce the real data. Reports fitted R₀, RMSE, R², and a residuals chart.
   - **Manual overlay mode** — lets you adjust parameters with sliders and instantly compare your simulated curve against the real observations, with live R² feedback.
3. Output the fitted parameter values as a copyable string that can be entered into the Simulation Controls to run the full dashboard using real-data-calibrated parameters.

### Step 6 — Export Results (📋 Data & Export Tab)

Download two CSV files for your report appendix:

- **Time-series CSV** — daily values for S, E, I, R, D, hospitalisation estimates, daily new cases (incidence), and time-varying Rt(t)
- **Scenario summary CSV** — all parameters and key epidemiological metrics in tabular form

---

## How Users Benefit

### For Students
EpiSim removes the mathematical barrier to epidemic modelling. A student can explore how changing a single parameter (e.g. doubling vaccination coverage) affects the peak, the deaths, and the herd immunity threshold — in real time, without writing code. The built-in insight annotations explain what each chart means, making the platform self-teaching.

### For Researchers
The parameter fitting capability allows researchers to calibrate a compartmental model to real outbreak data from any disease or region. The sensitivity tornado chart immediately identifies which parameters carry the most uncertainty — guiding where further data collection is most valuable.

### For Educators
The animated epidemic curve, phase-plane portrait, and Rt(t) chart are lecture-quality visualisations of core epidemiological concepts. Students can experiment interactively while the educator explains the underlying mathematics shown in the sidebar equation panel.

### For Public Health Analysis
The comparison tab directly answers the key policy question: *"What is the measurable impact of this intervention?"* Lives saved, infections averted, ICU pressure, and the shift in epidemic peak day are all quantified automatically.

---

## How to Run

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Run the dashboard

```powershell
.\run.bat
```

The dashboard opens automatically at `http://localhost:8501`.

---

## References

- Kermack, W.O. & McKendrick, A.G. (1927). *A contribution to the mathematical theory of epidemics.* Proceedings of the Royal Society A.
- Anderson, R.M. & May, R.M. (1991). *Infectious Diseases of Humans: Dynamics and Control.* Oxford University Press.
- Heesterbeek, H. et al. (2015). Modeling infectious disease dynamics in the complex landscape of global health. *Science*, 347(6227).
- World Health Organization. (2020). *COVID-19 Technical Guidance.* WHO.
