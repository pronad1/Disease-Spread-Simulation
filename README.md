# EpiSim — Disease Spread Simulation

A simple Python-based epidemic modeling project for academic use. The project implements a SEIR compartmental model and provides an interactive Streamlit dashboard for exploring how transmission, recovery, vaccination, and social distancing affect disease spread.

## What this project includes

- A SEIR simulation engine built with Python and SciPy
- A web dashboard built with Streamlit
- Adjustable parameters for:
  - population size
  - transmission rate $\beta$
  - incubation rate $\sigma$
  - recovery rate $\gamma$
  - initial infected count
  - vaccination coverage
  - distancing reduction
- Basic automated tests with pytest

## Project structure

- [episim.py](episim.py) — core simulation logic
- [ui/app.py](ui/app.py) — interactive dashboard
- [tests/test_episim.py](tests/test_episim.py) — test cases
- [requirements.txt](requirements.txt) — Python dependencies
- [description.ipynb](description.ipynb) — initial notebook idea and project description

## Model overview

The simulation uses the SEIR framework:

- $S$: Susceptible
- $E$: Exposed
- $I$: Infectious
- $R$: Recovered

The system follows the standard equations:

$$
\frac{dS}{dt} = -\beta \frac{SI}{N}
$$

$$
\frac{dE}{dt} = \beta \frac{SI}{N} - \sigma E
$$

$$
\frac{dI}{dt} = \sigma E - \gamma I
$$

$$
\frac{dR}{dt} = \gamma I
$$

## How to run

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Run the dashboard

```powershell
.\run.bat
```

## Academic use note

This project is suitable for a simulation sessional or coursework submission because it demonstrates:

- epidemic modeling fundamentals
- parameter-based scenario analysis
- public health intervention comparison
- a practical Python implementation with visualization

## Future improvements

Possible extensions include:

- adding an agent-based model
- comparing multiple disease types
- adding charts for peak infection and total cases
- exporting results as CSV or image
- adding a more advanced intervention timeline
