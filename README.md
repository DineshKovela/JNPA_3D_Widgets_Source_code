# TrafficTwin — 3D GIS traffic simulator

A working implementation of the reference architecture: GIS ingestion → canonical network model → multi-resolution simulation engines → analytics → 3D visualisation, built on the supplied study-area data.

> **Study area note.** The supplied files are named *Gandhinagar*, but their coordinates (EPSG:32643, ≈ 75.79 °E 26.87 °N) and attributes (Tonk Road, Gopalpura Bypass, city = JAIPUR) place the area in **Jaipur**. The app reports this on the Layers panel.

## Layout

```
pipeline/build_data.py   GIS pipeline (Python): raw GIS -> app-ready layers + data-quality report
web/shell.html           page shell (layout, design tokens, panels)
web/src/core.js          network model, turning movements + bans + conflicts, multi-phase signal plans, side friction,
                         IRC saturation flow, turn-aware (link-labelled) Dijkstra, PCU/vehicle classes
web/src/demand.js        4-step demand: generation, gravity (Furness), MNL mode choice, gateways, events
web/src/macro.js         static UE (conjugate Frank–Wolfe, Akçelik/BPR + HCM junction delays), GEH/R²/RMSE, ODME, emissions
web/src/meso.js          agent-based link transmission model (lane groups, backward wave) + multi-class porous CTM
web/src/micro.js         microsimulation: Human Driver Model, driver heterogeneity, area-based lateral + turn lanes,
                         movement-level junctions, bus dwell, pickups, parking manoeuvres, pedestrians, TTC, VSP CO2
web/src/analysis.js      Web Worker pool, replications + confidence intervals, hold-out validation, SPSA calibration,
                         travel-time validation
web/src/realtime.js      digital twin: Kalman LLT filter, forecast, incident detection, assimilation, exports
web/src/scene.js         Three.js 3D scene: DTM/DSM terrain + ortho, LoD1 buildings, draped road ribbons
web/src/anim3d.js        3D vehicle animators for the macro (steady-state flow), meso (queue agents) and CTM (speed-field
                         particles) engines, sharing the micro engine's interface
web/src/vehicles3d.js    3D vehicles: low-poly models per class, liveries, brake/indicator lights, shadows,
                         car-following links, conflict flashes, picking, follow and driver cameras
web/src/app.js           UI controller: 9 modules, inspector, legends, engines orchestration
build.py                 inlines the modules into web/index.html
test/                    Node engine tests (t1–t11) and Playwright browser tests (uitest5.py covers the realism features)
```

## Quick start

- **Easiest:** extract the zip, then double-click **`TrafficTwin.html`**. All data is built in and it opens straight from disk.
- **Multi-file version** (for editing data): double-click `run_windows.bat`, or run `./run_mac_linux.sh`. This needs Python and opens http://localhost:8000. Opening `web/index.html` directly from disk will not work, because browsers block `file://` pages from loading data files.

## Run it yourself

```bash
pip install rasterio geopandas shapely pyproj pillow numpy
python pipeline/build_data.py <folder with the raw GIS files> web/data
python build.py
cd web && python -m http.server 8000     # open http://localhost:8000
```

Self-hosted, the **Live → WebSocket** source connects to any feed that sends
`{"t": minuteOfDay, "readings": [{"link": 123, "flow": 840}]}`.

## What the pipeline does (`build_data.py`)

| Step | Detail |
|---|---|
| Ingest + CRS checks | All layers must share one projected CRS (here EPSG:32643, metres) |
| Terrain | DTM and DSM resampled to a 4 m grid, voids filled; slope statistics |
| Orthophoto | Palette → RGB, 4096 px texture plus a quick-load preview |
| Buildings | LoD1 footprints, base elevation, height, floors, floor area, inferred land use |
| One-way repair | Left-hand-traffic rule: the opposing carriageway must lie to the driver's right (67 of 101 segments reversed) |
| Topology | Endpoint snapping (3 m, 8 m onto arterials), noding per grade level |
| Flyovers | Level-1 chain ends joined to the ground network; deck height ramps over 70 m |
| U-turns, median openings | Dead-end carriageways linked; 41 median crossings added at side-road junctions |
| Link attributes | Lanes per direction, capacity (PCU/h), free-flow speed (class × surface × uphill penalty), DTM gradient and elevation profile |
| Junctions | Signal / priority / through typing; signals merged within 25 m |
| Zones | 24 TAZ by floor-area-weighted k-means; 34 boundary gateways (divided carriageways grouped) |
| Count stations | 80 CCTV-equipped link directions |
| Side friction | Commercial frontage (floor area within 30 m), on-street parking, pedestrian activity (0–3), friction class L/M/H/VH, bus stops on arterials every ~350 m |

## Engines

| Engine | Method | Outputs |
|---|---|---|
| Macro | Multi-class static UE on turn-aware routes; conjugate Frank–Wolfe with bisection. Mid-block cost: Akçelik (default) or BPR. Junction delay per approach: HCM uniform + overflow delay from IRC:SP:41 saturation flow and the movement's green share; gap-acceptance delay at priority junctions; turn penalties and bans. Signal–assignment loop with multi-phase Webster on turning flows | flow, turning flows, v/c, LOS, speed, junction delay, CO₂, VKT/VHT, convergence |
| Meso | Agent-based link transmission model: turn lane groups with their own queues and capacity, backward-wave storage release (spillback), movement-level signals, max-pressure, gap-acceptance capacity for minor movements, turn-aware reactive re-routing, 15-minute departure profile | 5-min link speeds/flows/occupancy, trip times, replay |
| Micro | Human Driver Model (reaction time, Wiener perception errors, emergency override) with per-driver parameter variation; area-based lateral movement and turn-lane positioning; curved junction paths; movement-level signals with permissive rights; gap acceptance against conflicting movements and conflict-area occupancy; two-wheeler creeping; bus dwell / bus bays; auto pickups; parking manoeuvres; pedestrians with gap acceptance | 3D vehicles, TTC and pedestrian conflicts, CO₂ (VSP on DEM grade), detector counts |
| CTM | Multi-class (cars + porous two-wheelers) Godunov CTM; junction diverges and side-street merges from the assigned turning flows; movement-level signals; incident capacity drop | time–space diagram, queue length, travel time, side flows |
| Real-time | Kalman local-linear-trend per station, 15-min forecast, z-score incident alerts, demand scaling | live estimates, alerts, re-assigned network |

## Realism, calibration and confidence

| Area | What the model does now | Where |
|---|---|---|
| Junctions | Every junction is a set of turning movements (L/T/R/U, left-hand traffic) with penalties, bans, crossing conflicts; bans that would disconnect the network are lifted automatically | Network panel |
| Signals | 2-phase (permitted rights), approach-split, or protected-right plans; free left turns; Webster on turning flows; max-pressure; import/export timing sheets (`node_id,plan,offset,green_1,…`) | Network panel, Scenarios |
| Side friction | Capacity × 1.00 / 0.93 / 0.84 / 0.74 and speed reductions by class; parking strip removed from the carriageway; scenario measures: parking ban, bus bays, pedestrian facilities | Scenarios → Realism, road layer “Side friction class” |
| Demand | Gateways capped by the downstream bottleneck; 15-minute departure profile; observed OD matrix import (`origin,destination,[class],trips`) | Demand panel |
| Calibration | ODME with hold-out stations (default 30%) reported separately; SPSA calibration of driver behaviour on counts; travel-time validation (≥85% of routes within ±15%) | Counts panel |
| Confidence | Replications for meso and micro in background Web Workers; mean, 95% CI, CV and runs needed for ±5% | Simulate → Meso / Micro |

## Interface

- **Layout:** a workbench-style widget with a slim title bar (scenario name, run status, report, hide command bar, full screen, light/dark), a full-bleed 3D scene, and notification cards in the top-right corner.
- **Command bar:** at the bottom centre, with tabs and icon commands:
  - **Experience:** GIS layers, network, results, report, reset view, top view.
  - **Create:** scenarios, demand, counts, vehicle classes.
  - **Simulate:** static, dynamic, micro 3D, CTM, start/pause, ride along.
  - **Tools:** isochrone, live twin, export, screenshot.
  - **Settings:** vehicle display, driver behaviour, theme.
  - **View:** orthophoto, hillshade, elevation, DSM, buildings, full screen.
- **Panels:** commands open floating panels with title bars.

## 3D vehicle visualisation (Simulate → Micro 3D)

- **Models:** each class has its own low-poly model, so the class is readable from the shape. The models are a two-wheeler with rider, bicycle with rider, car, auto-rickshaw with canopy, bus, LCV and a three-axle truck. They're coloured with street liveries, or by class, speed or driving state.
- **Smooth playback:** the 0.25 s physics steps are interpolated, so vehicles move smoothly at any playback speed.
- **Driving model on screen:**
  - brake lights glow when deceleration exceeds 0.8 m/s² or the vehicle is queued;
  - indicators blink while a vehicle moves sideways to filter or change position;
  - lines from follower to leader are coloured by time-to-collision;
  - rings flash where a TTC conflict or forced junction entry happens.
- **Driving states:** free flow, car-following, queued, braking for signal, stopped at red, yielding at junction, forcing entry.
- **Vehicle inspector:** click a vehicle to see its speed, acceleration, lateral position, leader, gap, TTC, next junction control, route and CO₂. Its remaining route is drawn as a dashed line.
- **Cameras:** orbit, follow vehicle, or driver's view. "Ride along" picks a random vehicle of a class. Esc returns to orbit.
- **Road surface:** the asphalt style shows centre lines, lane dividers and carriageway edge lines.

## 3D vehicles on every engine

All four engines can show 3D vehicles. Open **Simulate**, choose an engine, and press **Start 3D simulation**.

| Engine | What the 3D vehicles represent |
|---|---|
| Macro (static UE) | Steady-state flow. Vehicles are seeded at the assigned density (flow ÷ speed) per lane, cruise at congested link speeds, take turns in proportion to the assigned downstream flows, and stop at red signals using IDM following. |
| Meso (queue model) | The queue-model agents themselves. Each moves according to its link entry and exit times; vehicles that cannot leave stack up from the stop line, so spillback is visible. Includes a 3-minute warm-up. |
| Micro | The full microscopic model. |
| CTM corridor | Particles carried through the CTM speed field v(x, t). They stop on red at real stop lines, and their speed is capped in congested or incident cells, so queues and shockwaves appear as vehicles. |

On every engine you get the same 3D features: vehicle models, liveries, brake and indicator lights, velocity arrows, speed tags, the inspector, follow and driver cameras, and ride-along.

## Analysis assistant (Results panel)

**Built-in engine.** The insights engine needs no external service. It writes plain-language findings from the current results, with one topic per button:
- **Summary:** network state and the biggest lever.
- **Bottlenecks:** worst links, with suggested measures by road type and control.
- **Signals:** degree of saturation at signalised junctions.
- **Emissions:** CO₂ by class and hotspots.
- **Safety:** micro conflicts by location.
- **Calibration:** GEH and R².
- **Scenarios:** scenario deltas.

Typed questions are routed to the matching topic.

**Your own AI or analysis service.** To connect one, set it in the page head:

```js
window.TRAFFICTWIN_CONFIG = { assistantName: 'Analysis assistant', assistantUrl: 'https://your-host/api/traffic-assistant', assistantHeaders: { Authorization: 'Bearer …' } };
```

The app POSTs `{question, scenario, context, kpi}` and expects back `{answer}`. Here `context` is the markdown scenario report. If the service fails, the app falls back to the built-in insights.

## Default assumptions to replace with local data

- **Trip rates** are per 100 m² of floor area: residential 0.48 / 0.16, commercial 0.55 / 2.0, industrial 0.35 / 0.9.
- **Gateway loading** is 0.28 of capacity on arterials and 0.07 on local streets, capped by the downstream bottleneck.
- **Side-friction factors** follow Indo-HCM ranges but are indicative; calibrate them with local speed surveys.
- **Driver parameters** vary by ±10–20% around the class values; run the SPSA calibration with real counts.
- **Mode-choice coefficients** are illustrative.
- **Sample counts are synthetic.** Upload real ATCC/CCTV counts on the Counts panel, then run ODME.
- **Land use is inferred from geometry.** A land-use layer will improve trip generation.
- **The flood model is a DTM "bathtub".** It is not hydraulic.
- **Emission factors are indicative.** They use COPERT-style curves for the macro model and vehicle-specific power for the micro model.
