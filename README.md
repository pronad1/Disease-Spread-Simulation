<div align="center">

<br/>

# 🦠 EpiSim

### *Academic-Grade Epidemic Simulation Platform*

<br/>

[![Live Demo](https://img.shields.io/badge/▶%20Live%20Demo-disease--spread--simulation.streamlit.app-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://disease-spread-simulation.streamlit.app/)
&nbsp;
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
&nbsp;
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
&nbsp;
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> *"The goal of mathematical epidemiology is not merely to describe, but to illuminate — to reveal the hidden architecture of an epidemic before it reveals itself."*

<br/>

---

</div>

## Overview

**EpiSim** is an interactive, mathematically rigorous epidemic simulation platform built on compartmental ODE models. It bridges the gap between abstract epidemiological theory and intuitive, real-time exploration — empowering students, researchers, and public health analysts to model outbreak dynamics, calibrate against real-world data, and quantify the impact of interventions — all within a single, beautifully designed dashboard.

<br/>

<div align="center">

### [→ Launch the Live Platform](https://disease-spread-simulation.streamlit.app/)

*No installation. No setup. Open in any browser.*

</div>

<br/>

---

## Supported Epidemic Models

EpiSim implements four classical compartmental frameworks, each solving a coupled system of Ordinary Differential Equations in real time:

| Model | Compartments | Optimal Application |
|:-----:|:------------:|:-------------------|
| **SEIRD** | S → E → I → R / D | COVID-19, Ebola — full dynamics with incubation and explicit mortality |
| **SEIR** | S → E → I → R | Influenza — incubation period without direct mortality tracking |
| **SIR** | S → I → R | Classical Kermack–McKendrick outbreaks with permanent immunity |
| **SIS** | S → I → S | Bacterial infections — no lasting immunity, endemic equilibrium |

<br/>

---

## Mathematical Foundation

The SEIRD model governs population flow through five mutually exclusive health states:

$$\frac{dS}{dt} = -\beta \frac{SI}{N} \qquad \frac{dE}{dt} = \beta \frac{SI}{N} - \sigma E$$

$$\frac{dI}{dt} = \sigma E - (\gamma + \mu)I \qquad \frac{dR}{dt} = \gamma I \qquad \frac{dD}{dt} = \mu I$$

| Symbol | Parameter | Interpretation |
|:------:|:---------:|:--------------|
| **β** | Transmission rate | Effective contacts × probability of transmission per contact per day |
| **σ** | Incubation rate | Reciprocal of the mean latent period (days⁻¹) |
| **γ** | Recovery rate | Reciprocal of the mean infectious period (days⁻¹) |
| **μ** | Case fatality rate | Fraction of infectious-days terminating in death |
| **N** | Total population | Assumed closed, homogeneously mixing population |

<br/>

---

## Platform Capabilities

### 📈 Simulation Dashboard
Animated, day-by-day epidemic curve with a scrubable timeline slider. Six academic metric cards update instantaneously with every parameter change:

| Metric | Description |
|:-------|:-----------|
| **R₀** | Basic reproduction number — mean secondary infections per primary case |
| **Peak Active Infections** | Maximum simultaneous infectious burden |
| **Peak Hospitalisations** | Hospital demand relative to configured ICU capacity |
| **Total Deaths** | Cumulative mortality and Case Fatality Ratio |
| **Herd Immunity Threshold** | Critical immunisation fraction: 1 − 1/R₀ |
| **Doubling Time** | Characteristic exponential growth timescale (days) |

<br/>

### 🔬 Advanced Epidemiological Analysis
Four publication-quality scientific visualisations:

- **Incidence Curve** — Daily new cases (dI/dt), with surge-period highlighting above the 80th percentile
- **Effective Reproduction Number Rₜ(t)** — Time-varying transmission dynamics; green threshold at Rₜ = 1.0 marks epidemic control
- **Phase-Plane Portrait (S–I Trajectory)** — State-space trajectory spiraling from high-S/low-I toward endemic equilibrium; isocline at S = N/R₀ marks the epidemic peak
- **Sensitivity / Tornado Analysis** — ±20% parameter sweep revealing which variables most critically govern peak infection magnitude

<br/>

### ⚖️ Scenario Comparison
Side-by-side overlay of a no-intervention baseline against the current policy scenario:
- *"Flatten the curve"* composite chart with ICU threshold marker
- Rₜ(t) comparative trajectories
- Headline impact summary: **lives saved** and **peak infections averted**
- Full metric breakdown table with absolute and relative change columns

<br/>

### 📂 Real-World Data Fitting
Upload any outbreak CSV (WHO situation reports, national case counts) and EpiSim will:
1. Preview and map your columns (Day, Active Cases, Deaths)
2. **Auto-fit** — L-BFGS-B least-squares optimisation returning calibrated β, σ, γ, μ with fitted R₀, RMSE, R², and a residuals chart
3. **Manual overlay** — Interactive slider fitting with live R² feedback against observed data

<br/>

### 📋 Data Export
Download analysis-ready CSV files for academic appendices:
- **Time-series export** — S, E, I, R, D, hospitalisations, daily incidence, and Rₜ(t)
- **Scenario summary** — All configured parameters and derived epidemiological metrics

<br/>

---

## Who It's For

<table>
<tr>
<td width="50%" valign="top">

**🎓 Students**

Explore how a single parameter shift — doubling vaccination coverage, halving contact rates — propagates through the entire epidemic curve. Built-in chart annotations make the platform self-teaching, removing the mathematical barrier to epidemic modelling.

</td>
<td width="50%" valign="top">

**🔭 Researchers**

Calibrate compartmental models to real outbreak data from any disease or region. The sensitivity tornado chart immediately surfaces which parameters carry the highest epistemic uncertainty — pinpointing where further data collection yields the greatest analytical value.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**📚 Educators**

Animated epidemic curves, phase-plane portraits, and Rₜ(t) trajectories are lecture-ready visualisations of core epidemiological concepts. Students experiment interactively while the instructor narrates the underlying mathematics from the sidebar equation panel.

</td>
<td width="50%" valign="top">

**🏥 Public Health Analysts**

The Comparison tab directly answers the policy question: *"What is the quantified impact of this intervention?"* Lives saved, infections averted, ICU headroom, and peak-day shift — all computed automatically.

</td>
</tr>
</table>

<br/>

---

## Running Locally

```powershell
# 1. Clone the repository
git clone https://github.com/pronad1/Disease-Spread-Simulation.git
cd Disease-Spread-Simulation

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
.\run.bat
```

The dashboard opens automatically at `http://localhost:8501`.

> **Alternatively**, access the fully hosted platform instantly at **[disease-spread-simulation.streamlit.app](https://disease-spread-simulation.streamlit.app/)** — no local setup required.

<br/>

---

## Tech Stack

| Layer | Technology |
|:------|:----------|
| **Frontend / Dashboard** | [Streamlit](https://streamlit.io/) |
| **Scientific Computing** | [NumPy](https://numpy.org/), [SciPy](https://scipy.org/) (ODE integration, L-BFGS-B optimisation) |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) |
| **Visualisation** | [Plotly](https://plotly.com/python/) (animated figures, phase portraits) |
| **Deployment** | [Streamlit Community Cloud](https://streamlit.io/cloud) |

<br/>

---

## References

- Kermack, W.O. & McKendrick, A.G. (1927). *A contribution to the mathematical theory of epidemics.* **Proceedings of the Royal Society A**, 115(772), 700–721.
- Anderson, R.M. & May, R.M. (1991). *Infectious Diseases of Humans: Dynamics and Control.* Oxford University Press.
- Heesterbeek, H. et al. (2015). Modeling infectious disease dynamics in the complex landscape of global health. ***Science***, 347(6227), aaa4339.
- World Health Organization. (2020). *COVID-19 Technical Guidance.* WHO Press.

<br/>

---

<div align="center">

Built with precision for the epidemiological community.

**[→ Experience EpiSim Live](https://disease-spread-simulation.streamlit.app/)**


<br/>

*© 2025 EpiSim — Open Source under the MIT License*

</div>
