"""
app.py — EcoMind Smart Waste AI  (3D Enhanced Version)
Fixes: Festival defaults, dead fields, composition validation
3D: Three.js globe, Plotly 3D surface, particle system, animated counters
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="EcoMind — Smart Waste AI",
    page_icon="♻",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "https://smart-waste-backend-vtop.onrender.com"

# ── FULL CSS (same cyberpunk as original) ──────────────────────
st.markdown("""<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600&family=Share+Tech+Mono&display=swap');
  html,body,[class*="css"]{font-family:'Rajdhani',sans-serif!important;background:#020b06!important;color:#e0ffe0!important}
  .stApp{background:radial-gradient(ellipse at 20% 20%,#021a08 0%,#020b06 50%,#000d04 100%)!important}
  .stApp::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;
    background-image:linear-gradient(rgba(0,255,80,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,80,.03) 1px,transparent 1px);
    background-size:40px 40px;pointer-events:none;z-index:0}
  [data-testid="stMetricValue"]{font-family:'Orbitron',sans-serif!important;font-size:1.8rem!important;font-weight:700!important;color:#00ff50!important;text-shadow:0 0 20px rgba(0,255,80,.5)!important}
  .stButton>button{font-family:'Orbitron',sans-serif!important;font-weight:700!important;font-size:.72rem!important;letter-spacing:.15em!important;
    background:linear-gradient(135deg,rgba(0,255,80,.1),rgba(0,180,60,.05))!important;color:#00ff50!important;
    border:1px solid rgba(0,255,80,.4)!important;border-radius:4px!important;padding:.8rem 2rem!important;
    text-transform:uppercase!important;transition:all .3s!important}
  .stButton>button:hover{background:linear-gradient(135deg,rgba(0,255,80,.2),rgba(0,180,60,.1))!important;
    border-color:#00ff50!important;box-shadow:0 0 40px rgba(0,255,80,.3)!important;color:#fff!important;transform:translateY(-1px)!important}
  .eco-result-main{background:linear-gradient(135deg,rgba(0,255,80,.08),rgba(0,0,0,.5));border:1px solid rgba(0,255,80,.3);
    border-radius:6px;padding:3rem 2rem;text-align:center;position:relative;overflow:hidden;box-shadow:0 0 60px rgba(0,255,80,.1)}
  .eco-result-main::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#00ff50,transparent)}
  .eco-result-num{font-family:'Orbitron',sans-serif;font-size:4rem;font-weight:900;color:#00ff50;line-height:1;text-shadow:0 0 40px rgba(0,255,80,.6)}
  .eco-route-stop{display:flex;align-items:center;gap:.75rem;background:rgba(0,255,80,.03);border:1px solid rgba(0,255,80,.12);
    border-left:3px solid rgba(0,255,80,.2);padding:.75rem 1rem;margin:5px 0;border-radius:0 4px 4px 0;transition:all .3s}
  .eco-pill-green{background:rgba(0,255,80,.1);border:1px solid rgba(0,255,80,.4);color:#00ff50;
    padding:3px 12px;border-radius:100px;font-family:'Share Tech Mono',monospace;font-size:.58rem;letter-spacing:.1em;text-transform:uppercase}
  /* NEW: pulsing status */
  @keyframes pulse-ring{0%{box-shadow:0 0 0 0 rgba(0,255,80,.6)}100%{box-shadow:0 0 0 12px rgba(0,255,80,0)}}
  .pulse-online{animation:pulse-ring 1.5s infinite;border-radius:100px}
  @keyframes count-up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  .count-anim{animation:count-up .6s ease-out}
</style>""", unsafe_allow_html=True)


# ── 3D: PARTICLE SYSTEM HEADER ─────────────────────────────────
def render_particle_header():
    components.html("""
    <canvas id="pc" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0"></canvas>
    <div style="position:relative;z-index:1;background:linear-gradient(135deg,rgba(0,255,80,.08),rgba(0,0,0,.6));
      border:1px solid rgba(0,255,80,.25);border-radius:8px;padding:2.5rem 3rem;text-align:center">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#00ff50 40%,rgba(0,255,80,.3) 70%,transparent)"></div>
      <div style="font-family:'Orbitron',sans-serif;font-size:2.4rem;font-weight:900;color:#00ff50;text-shadow:0 0 40px rgba(0,255,80,.5)">♻ ECOMIND</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:.7rem;letter-spacing:.25em;color:rgba(0,255,80,.4)">
        SMART WASTE AI · WATER DEMAND · WASTE GENERATION · ROUTE OPTIMIZATION
      </div>
    </div>
    <script>
    const c=document.getElementById('pc');
    c.width=c.offsetWidth||900; c.height=140;
    const ctx=c.getContext('2d');
    const pts=Array.from({length:80},()=>({
      x:Math.random()*c.width, y:Math.random()*c.height,
      vx:(Math.random()-.5)*.4, vy:-Math.random()*.5-.1,
      r:Math.random()*2+.5, a:Math.random()
    }));
    function draw(){
      ctx.clearRect(0,0,c.width,c.height);
      pts.forEach(p=>{
        p.x+=p.vx; p.y+=p.vy; p.a-=.003;
        if(p.y<0||p.a<=0){p.y=c.height;p.a=Math.random()*.8+.2;p.x=Math.random()*c.width}
        ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
        ctx.fillStyle=`rgba(0,255,80,${p.a})`;ctx.fill();
      });
      requestAnimationFrame(draw);
    }
    draw();
    </script>
    """, height=140)


# ── 3D: ROTATING GLOBE with waste pins ─────────────────────────
def render_3d_globe(stops=None, ordered_route=None):
    import json

    stops_js = json.dumps([{
        "lat": s["lat"], "lon": s["lon"],
        "name": s.get("name", ""),
        "fill": s.get("fill_percent", s.get("fill", 0))
    } for s in (stops or [])])

    route_js = json.dumps([{
        "lat": s["lat"], "lon": s["lon"],
        "name": s.get("name", ""),
        "fill": s.get("fill_percent", s.get("fill", 0))
    } for s in (ordered_route or [])])

    has_route = "true" if ordered_route else "false"

    components.html(f"""
    <div id="globe-container" style="width:100%;height:450px;background:#010f04;
      border:1px solid rgba(0,255,80,.25);border-radius:10px;
      overflow:hidden;position:relative;">

      <canvas id="gc" style="width:100%;height:100%"></canvas>

      <div style="position:absolute;top:12px;left:14px;font-family:monospace;
        font-size:.6rem;color:rgba(0,255,80,.5);letter-spacing:.15em;line-height:2;">
        THREE.JS · WEBGL · LIVE PINS<br>
        <span style="color:rgba(0,255,80,.3)">DRAG TO ROTATE · SCROLL TO ZOOM</span>
      </div>

      <div style="position:absolute;top:12px;right:14px;font-family:monospace;
        font-size:.58rem;color:rgba(0,255,80,.4);text-align:right;line-height:2;">
        <span style="color:#00ff50">●</span> Normal &nbsp;
        <span style="color:#ffaa00">●</span> Medium &nbsp;
        <span style="color:#ff4444">●</span> Urgent
      </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
    const STOPS     = {stops_js};
    const ROUTE     = {route_js};
    const HAS_ROUTE = {has_route};

    const container = document.getElementById('globe-container');
    const W = container.clientWidth  || 700;
    const H = container.clientHeight || 450;

    const renderer = new THREE.WebGLRenderer({{
      canvas: document.getElementById('gc'),
      antialias: true, alpha: true
    }});
    renderer.setSize(W, H);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x010f04, 1);

    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, W/H, 0.1, 1000);
    camera.position.set(0, 0, 2.2);  // ← zoomed in closer

    // ── GROUP everything so it all rotates together ──────────
    const earthGroup = new THREE.Group();
    scene.add(earthGroup);

    // Globe sphere
    const globe = new THREE.Mesh(
      new THREE.SphereGeometry(1, 64, 64),
      new THREE.MeshPhongMaterial({{
        color:     0x021a08,
        emissive:  0x002208,
        specular:  0x00ff50,
        shininess: 20,
        transparent: true,
        opacity: 0.95
      }})
    );
    earthGroup.add(globe);

    // Wireframe overlay — inside same group so it rotates too
    earthGroup.add(new THREE.Mesh(
      new THREE.SphereGeometry(1.002, 32, 32),
      new THREE.MeshBasicMaterial({{
        color: 0x00ff50, wireframe: true,
        transparent: true, opacity: 0.06
      }})
    ));

    // Atmosphere glow
    earthGroup.add(new THREE.Mesh(
      new THREE.SphereGeometry(1.15, 32, 32),
      new THREE.MeshBasicMaterial({{
        color: 0x00ff50, transparent: true,
        opacity: 0.04, side: THREE.BackSide
      }})
    ));

    // ── Lights ───────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0x003310, 4));
    const dLight = new THREE.DirectionalLight(0x00ff50, 1.5);
    dLight.position.set(5, 3, 5);
    scene.add(dLight);

    // ── Lat/Lon → 3D ─────────────────────────────────────────
    function ll3d(lat, lon, r=1.0) {{
      const phi   = (90 - lat) * Math.PI / 180;
      const theta = (lon + 180) * Math.PI / 180;
      return new THREE.Vector3(
        -r * Math.sin(phi) * Math.cos(theta),
         r * Math.cos(phi),
         r * Math.sin(phi) * Math.sin(theta)
      );
    }}

    function pinColor(fill) {{
      if (fill >= 85) return 0xff4444;
      if (fill >= 70) return 0xffaa00;
      return 0x00ff50;
    }}

    // ── Stop Pins — added to earthGroup so they rotate ───────
    const pulseRings = [];

    const stopsToPlot = STOPS.length > 0 ? STOPS : [
      {{lat:17.385, lon:78.487, name:"Hyderabad", fill:0}}
    ];

    stopsToPlot.forEach((s, i) => {{
      const pos = ll3d(s.lat, s.lon, 1.0);
      const col = pinColor(s.fill);

      // Pin dot — bigger (0.04)
      const pin = new THREE.Mesh(
        new THREE.SphereGeometry(0.04, 12, 12),
        new THREE.MeshBasicMaterial({{ color: col }})
      );
      pin.position.copy(pos.clone().multiplyScalar(1.02));
      earthGroup.add(pin);

      // Spike outward
      const spike = new THREE.Mesh(
        new THREE.CylinderGeometry(0.004, 0.001, 0.1, 6),
        new THREE.MeshBasicMaterial({{
          color: col, transparent: true, opacity: 0.8
        }})
      );
      spike.position.copy(pos.clone().multiplyScalar(1.07));
      spike.lookAt(new THREE.Vector3(0, 0, 0));
      spike.rotateX(Math.PI / 2);
      earthGroup.add(spike);

      // Pulse ring — bigger (0.05, 0.07)
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.05, 0.07, 16),
        new THREE.MeshBasicMaterial({{
          color: col, transparent: true,
          opacity: 0.7, side: THREE.DoubleSide
        }})
      );
      ring.position.copy(pos.clone().multiplyScalar(1.025));
      ring.lookAt(new THREE.Vector3(0, 0, 0));
      ring.userData.phase = i * 0.8;
      earthGroup.add(ring);
      pulseRings.push(ring);
    }});

    // ── Route Lines + Travelling Dots ─────────────────────────
    const travelDots = [];

    if (HAS_ROUTE && ROUTE.length > 1) {{
      for (let i = 0; i < ROUTE.length - 1; i++) {{
        const A   = ll3d(ROUTE[i].lat,   ROUTE[i].lon,   1.04);
        const B   = ll3d(ROUTE[i+1].lat, ROUTE[i+1].lon, 1.04);
        const mid = A.clone().add(B).multiplyScalar(0.5)
                     .normalize().multiplyScalar(1.22);

        const curve = new THREE.QuadraticBezierCurve3(A, mid, B);
        const pts   = curve.getPoints(50);

        // Glowing arc line
        const line = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints(pts),
          new THREE.LineBasicMaterial({{
            color: 0x00ff50, transparent: true, opacity: 0.9
          }})
        );
        earthGroup.add(line);

        // Travelling dot along arc
        const dot = new THREE.Mesh(
          new THREE.SphereGeometry(0.02, 8, 8),
          new THREE.MeshBasicMaterial({{ color: 0x00ffaa }})
        );
        dot.position.copy(A);
        earthGroup.add(dot);
        travelDots.push({{
          mesh: dot, curve: curve,
          progress: i / ROUTE.length
        }});

        // Stop order marker
        const marker = new THREE.Mesh(
          new THREE.SphereGeometry(0.032, 10, 10),
          new THREE.MeshBasicMaterial({{
            color: 0x00ffaa, transparent: true, opacity: 0.95
          }})
        );
        marker.position.copy(A.clone().multiplyScalar(1.03));
        earthGroup.add(marker);
      }}
    }}

    // ── Start facing India (Hyderabad lon=78°) ────────────────
    earthGroup.rotation.y = -1.36;  // 78° in radians

    // ── Mouse Drag ────────────────────────────────────────────
    let isDragging = false, prevX = 0, prevY = 0;
    let autoRotate = true;

    container.addEventListener('mousedown', e => {{
      isDragging = true;
      autoRotate = false;
      prevX = e.clientX;
      prevY = e.clientY;
    }});
    window.addEventListener('mouseup', () => {{
      isDragging = false;
      setTimeout(() => {{ autoRotate = true; }}, 3000);
    }});
    window.addEventListener('mousemove', e => {{
      if (!isDragging) return;
      // Rotate the whole earthGroup together
      earthGroup.rotation.y += (e.clientX - prevX) * 0.005;
      earthGroup.rotation.x += (e.clientY - prevY) * 0.003;
      prevX = e.clientX;
      prevY = e.clientY;
    }});

    // Scroll to zoom
    container.addEventListener('wheel', e => {{
      camera.position.z = Math.max(1.5,
        Math.min(5.0, camera.position.z + e.deltaY * 0.003));
      e.preventDefault();
    }}, {{passive: false}});

    // ── Camera Flyover (after optimization) ───────────────────
    let flyIndex  = 0;
    let flyT      = 0;
    let flyActive = false;
    if (HAS_ROUTE && ROUTE.length > 1) {{
      setTimeout(() => {{ flyActive = true; }}, 1500);
    }}

    // ── Animation Loop ────────────────────────────────────────
    let t = 0;
    function animate() {{
      requestAnimationFrame(animate);
      t += 0.016;

      // Auto rotate whole group
      if (autoRotate && !isDragging) {{
        earthGroup.rotation.y += 0.003;
      }}

      // Pulse rings
      pulseRings.forEach(ring => {{
        const sc = 1 + 0.4 * Math.abs(Math.sin(t * 2.5 + ring.userData.phase));
        ring.scale.set(sc, sc, sc);
        ring.material.opacity = 0.3 + 0.5 * Math.abs(Math.sin(t * 2.5 + ring.userData.phase));
      }});

      // Travelling dots along route
      travelDots.forEach(d => {{
        d.progress = (d.progress + 0.005) % 1;
        d.mesh.position.copy(d.curve.getPoint(d.progress));
      }});

      // Camera flyover between stops
      if (flyActive && !isDragging && ROUTE.length > 1) {{
        flyT += 0.005;
        if (flyT >= 1.0) {{
          flyT = 0;
          flyIndex = (flyIndex + 1) % (ROUTE.length - 1);
        }}
        const next = flyIndex + 1;
        const camA = ll3d(ROUTE[flyIndex].lat, ROUTE[flyIndex].lon, 2.5);
        const camB = ll3d(ROUTE[next].lat,     ROUTE[next].lon,     2.5);
        const smooth = flyT * flyT * (3 - 2 * flyT);
        camera.position.lerpVectors(camA, camB, smooth);
        camera.lookAt(0, 0, 0);
      }}

      renderer.render(scene, camera);
    }}

    animate();
    </script>
    """, height=460)
```

---

## The Key Fix Explained
```
OLD CODE — separate objects, pins don't follow globe:
  scene.add(globe)       ← rotates
  scene.add(wireframe)   ← doesn't rotate
  scene.add(pin)         ← doesn't rotate
  globe.rotation.y += X  ← only globe moves!

NEW CODE — everything in ONE group:
  earthGroup.add(globe)
  earthGroup.add(wireframe)
  earthGroup.add(pin)
  earthGroup.rotation.y += X  ← EVERYTHING moves together!


# ── 3D: PLOTLY SURFACE CHART ────────────────────────────────────
def render_3d_surface(pred_value):
    temps = np.linspace(15, 48, 30)
    pops  = np.linspace(10000, 200000, 30)
    T, P  = np.meshgrid(temps, pops)
    # Simulated surface based on prediction
    base  = pred_value
    Z     = base * (0.6 + 0.4*(T/48) + 0.3*(P/200000) - 0.1*np.sin(T/10))

    fig = go.Figure(data=[go.Surface(
        z=Z, x=T, y=P/1000,
        colorscale=[[0,"#010f04"],[0.3,"#003310"],[0.6,"#00aa35"],[1,"#00ff50"]],
        showscale=False,
        contours=dict(z=dict(show=True, usecolormap=True, project_z=True))
    )])
    fig.update_layout(
        height=380,
        paper_bgcolor="rgba(1,15,4,0)",
        plot_bgcolor="rgba(1,15,4,0)",
        scene=dict(
            xaxis=dict(title="Temp °C", gridcolor="rgba(0,255,80,.1)", backgroundcolor="rgba(1,15,4,0)", color="#00ff50"),
            yaxis=dict(title="Pop (k)", gridcolor="rgba(0,255,80,.1)", backgroundcolor="rgba(1,15,4,0)", color="#00ff50"),
            zaxis=dict(title="Demand L", gridcolor="rgba(0,255,80,.1)", backgroundcolor="rgba(1,15,4,0)", color="#00ff50"),
            bgcolor="rgba(1,15,4,0)",
        ),
        margin=dict(l=0,r=0,t=0,b=0),
        font=dict(color="#00ff50", family="Share Tech Mono"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── ANIMATED COUNTER ────────────────────────────────────────────
def render_animated_counter(label, value, unit, lo, hi):
    components.html(f"""
    <div style="background:linear-gradient(135deg,rgba(0,255,80,.08),rgba(0,0,0,.5));
      border:1px solid rgba(0,255,80,.3);border-radius:6px;padding:2.5rem 2rem;text-align:center;position:relative;overflow:hidden">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#00ff50,transparent)"></div>
      <div style="font-family:'Orbitron',sans-serif;font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:rgba(0,255,80,.5);margin-bottom:.75rem">{label}</div>
      <div id="counter" style="font-family:'Orbitron',sans-serif;font-size:3.8rem;font-weight:900;color:#00ff50;line-height:1;text-shadow:0 0 40px rgba(0,255,80,.6)">0</div>
      <div style="font-family:'Rajdhani',sans-serif;font-size:.9rem;color:rgba(0,255,80,.4);margin-top:.5rem">{unit}</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:.68rem;color:rgba(0,255,80,.3);margin-top:1rem;
        border-top:1px solid rgba(0,255,80,.1);padding-top:.75rem">95% CI &nbsp;|&nbsp; {lo} &ndash; {hi}</div>
    </div>
    <script>
    const target={value};
    const el=document.getElementById('counter');
    const fmt=n=>n>=1000?n.toLocaleString('en-IN',{{maximumFractionDigits:0}}):n.toFixed(2);
    let current=0, steps=60;
    const inc=target/steps;
    const timer=setInterval(()=>{{
      current=Math.min(current+inc,target);
      el.textContent=fmt(current);
      if(current>=target)clearInterval(timer);
    }},16);
    </script>
    """, height=220)


# ── API HELPERS ─────────────────────────────────────────────────
def api_post(endpoint, payload):
    try:
        r = requests.post(f"{API}{endpoint}", json=payload, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend."}
    except Exception as e:
        return {"error": str(e)}

def api_get(endpoint):
    try:
        r = requests.get(f"{API}{endpoint}", timeout=60)
        return r.json()
    except:
        return {"status": "offline"}


# ── SIDEBAR ─────────────────────────────────────────────────────
with st.sidebar:
    st.info("⏳ Backend may take 50s to wake. Wait and refresh!")
    st.markdown('<div style="font-family:Orbitron,sans-serif;font-size:1.3rem;font-weight:700;color:#00ff50;text-shadow:0 0 20px rgba(0,255,80,.5)">♻ EcoMind</div>', unsafe_allow_html=True)

    health = api_get("/health")
    status = health.get("status","offline")
    if status == "ready":
        # FIX: pulsing animation for online status
        st.markdown('<span class="eco-pill-green pulse-online">● Backend Online</span>', unsafe_allow_html=True)
    elif status == "models_not_trained":
        st.markdown('<span style="color:#ffaa00;font-family:monospace;font-size:.7rem">⚠ Models Not Trained</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#ff4444;font-family:monospace;font-size:.7rem">✕ Backend Offline</span>', unsafe_allow_html=True)

    metrics_data = health.get("metrics", {})
    if metrics_data:
        st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.55rem;letter-spacing:.15em;text-transform:uppercase;color:rgba(0,255,80,.3)">MODEL PERFORMANCE</div>', unsafe_allow_html=True)
        for name, m in metrics_data.items():
            r2  = m.get("r2", 0)
            col = "#00ff50" if r2 > 0.9 else "#ffaa00" if r2 > 0.7 else "#ff4444"
            st.markdown(f"""<div style="background:rgba(0,255,80,.03);border:1px solid rgba(0,255,80,.12);
              padding:.75rem 1rem;margin:5px 0;border-radius:4px">
              <div style="font-family:Share Tech Mono,monospace;font-size:.55rem;color:rgba(0,255,80,.3);text-transform:uppercase">{name}</div>
              <div style="font-family:Orbitron,sans-serif;font-weight:700;font-size:1.1rem;color:{col}">R² {r2:.3f}</div>
              <div style="font-family:Share Tech Mono,monospace;font-size:.6rem;color:rgba(0,255,80,.25)">MAE {m.get('mae',0):.2f} · RMSE {m.get('rmse',0):.2f}</div>
            </div>""", unsafe_allow_html=True)


# ── PAGE HEADER with particles ──────────────────────────────────
render_particle_header()
st.markdown("<br>", unsafe_allow_html=True)


# ── TABS ────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "▸ 01   Water Demand",
    "▸ 02   Waste Generation",
    "▸ 03   Route Optimization",
])


# ══════════════════════════════════════════════════════════════
# TAB 1 — WATER DEMAND
# ══════════════════════════════════════════════════════════════
with tab1:
    col_form, _, col_result = st.columns([1.05, 0.05, 1])

    with col_form:
        st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:rgba(0,255,80,.4);margin-bottom:6px">Area & Demographics</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        pop     = c1.number_input("Population", 1000, 1000000, 27836, step=1000)
        pop_den = c2.number_input("Pop. Density /km²", 100.0, 50000.0, 22342.0)
        hh_size = c1.number_input("Household Size", 1, 12, 6)
        income  = c2.number_input("Per Capita Income ₹", 50000, 1000000, 355551, step=10000)
        urban   = c1.selectbox("Urban / Rural", ["Urban","Rural"])
        c3, c4 = st.columns(2)
        temp     = c3.slider("Temperature °C", 5.0, 50.0, 35.4)
        rain     = c4.slider("Rainfall mm", 0.0, 400.0, 182.5)
        humidity = c3.slider("Humidity %", 10.0, 100.0, 71.6)
        season   = c4.selectbox("Season", ["Summer","Monsoon","Winter"])
        c5, c6 = st.columns(2)
        day_type   = c5.selectbox("Day Type", ["Weekday","Weekend"])
        # FIX 2: Correct festival options matching encoder
        festival   = c6.selectbox("Festival", ["No_Festival","Local_Festival","National_Festival"])
        past_water = st.number_input("Past Water Usage L", 50.0, 800.0, 399.29)
        recycle    = st.slider("Recycling Rate %", 0.0, 100.0, 30.7)
        sel_date   = st.date_input("Forecast Date", date.today())
        predict_water_btn = st.button("▸ Predict Water Demand", use_container_width=True)

    with col_result:
        if predict_water_btn:
            d = sel_date
            # FIX 1: No dayofyear, correct Festival/Disaster defaults
            payload = {
                "Population": pop, "Population_Density": pop_den,
                "Household_Size": hh_size, "Per_Capita_Income": income,
                "Urban_Rural_Type": urban, "Temperature_C": temp,
                "Rainfall_mm": rain, "Humidity_percent": humidity,
                "Season": season, "Day_Type": day_type,
                "Festival_Event": festival,
                "Disaster_Event": "No_Disaster",   # FIX 1
                "Past_Water_Usage": past_water,
                "Recycling_Rate_percent": recycle,
                "month": d.month, "dayofweek": d.weekday()
                # FIX 1: dayofyear REMOVED
            }
            with st.spinner("Running model inference…"):
                resp = api_post("/predict/water", payload)
            if "error" in resp:
                st.error(resp["error"])
            else:
                pred = resp["prediction"]
                val  = pred["water_demand_liters"]
                lo   = pred["lower_bound"]
                hi   = pred["upper_bound"]
                # 3D ENHANCEMENT: animated counter instead of static box
                render_animated_counter("Predicted Water Demand", val, "Litres / Day", f"{lo:,.0f} L", f"{hi:,.0f} L")
                st.markdown("<br>", unsafe_allow_html=True)
                # FIX 4: Real feature importances from /health
                fi = health.get("metrics",{}).get("water",{}).get("feature_importances",{})
                if fi:
                    st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.6rem;letter-spacing:.15em;color:rgba(0,255,80,.4)">FEATURE IMPORTANCE (from model)</div>', unsafe_allow_html=True)
                    fi_df = pd.DataFrame(list(fi.items())[:8], columns=["Feature","Importance"])
                    st.bar_chart(fi_df.set_index("Feature"), color="#00ff50", height=200)
                st.markdown("<br>", unsafe_allow_html=True)
                # 3D ENHANCEMENT: Plotly 3D surface
                st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.6rem;letter-spacing:.15em;color:rgba(0,255,80,.4)">3D DEMAND SURFACE: Temperature × Population</div>', unsafe_allow_html=True)
                render_3d_surface(val)
        else:
            st.markdown('<div style="background:rgba(0,255,80,.02);border:1px dashed rgba(0,255,80,.15);border-radius:6px;padding:4rem 2rem;text-align:center"><div style="font-family:Orbitron,sans-serif;font-size:.85rem;color:rgba(0,255,80,.3)">Set parameters and run prediction</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — WASTE GENERATION
# ══════════════════════════════════════════════════════════════
with tab2:
    col_wf, _, col_wr = st.columns([1.05, 0.05, 1])

    with col_wf:
        w_c1, w_c2 = st.columns(2)
        w_pop   = w_c1.number_input("Population", 1000, 1000000, 122028, step=1000, key="w2_pop")
        w_pd    = w_c2.number_input("Pop. Density /km²", 100.0, 50000.0, 20969.0, key="w2_pd")
        w_c3, w_c4 = st.columns(2)
        w_temp   = w_c3.slider("Temperature °C", 5.0, 50.0, 40.4, key="w2_t")
        w_rain   = w_c4.slider("Rainfall mm", 0.0, 400.0, 190.8, key="w2_r")
        w_season = w_c3.selectbox("Season", ["Summer","Monsoon","Winter"], key="w2_s")
        w_day    = w_c4.selectbox("Day Type", ["Weekday","Weekend"], key="w2_d")
        # FIX 2: Correct festival options
        w_fest   = w_c3.selectbox("Festival", ["No_Festival","Local_Festival","National_Festival"], key="w2_f")
        wh1, wh2, wh3 = st.columns(3)
        w_t1  = wh1.number_input("Yesterday t", 10.0, 600.0, 481.94, key="w2_t1")
        w_t7  = wh2.number_input("Last 7d t", 100.0, 5000.0, 3201.32, key="w2_t7")
        w_t30 = wh3.number_input("Last 30d t", 500.0, 20000.0, 6325.58, key="w2_t30")
        wo1, wo2 = st.columns(2)
        w_org = wo1.slider("Organic %",  0.0, 100.0, 45.8, key="w2_org")
        w_pla = wo2.slider("Plastic %",  0.0, 100.0, 27.3, key="w2_pla")
        w_pap = wo1.slider("Paper %",    0.0, 100.0, 9.8,  key="w2_pap")
        w_oth = wo2.slider("Other %",    0.0, 100.0, 12.1, key="w2_oth")

        # FIX 5: Composition validation
        total_comp = w_org + w_pla + w_pap + w_oth
        if total_comp > 100:
            st.warning(f"⚠️ Waste composition totals {total_comp:.1f}% — must be ≤ 100%. Adjust sliders.")

        w_coll = st.number_input("Collection Freq / week", 1, 7, 5, key="w2_coll")
        w_rec  = st.slider("Recycling Rate %", 0.0, 100.0, 25.1, key="w2_rec")
        w_date = st.date_input("Forecast Date", date.today(), key="w2_date")

        predict_waste_btn = st.button(
            "▸ Predict Waste Generation",
            use_container_width=True,
            key="w2_btn",
            disabled=(total_comp > 100)  # FIX 5
        )

    with col_wr:
        if predict_waste_btn:
            d = w_date
            # FIX 3: Only 19 fields that match WASTE_FEATURES exactly
            # FIX 1: No dayofyear, correct Festival/Disaster
            payload = {
                "Population": w_pop, "Population_Density": w_pd,
                "Temperature_C": w_temp, "Rainfall_mm": w_rain,
                "Season": w_season, "Day_Type": w_day,
                "Festival_Event": w_fest,
                "Disaster_Event": "No_Disaster",       # FIX 1
                "Past_Waste_t1_tons": w_t1,
                "Past_Waste_t7_tons": w_t7,
                "Past_Waste_t30_tons": w_t30,
                "Organic_Waste_percent": w_org,
                "Plastic_Waste_percent": w_pla,
                "Paper_Waste_percent": w_pap,
                "Other_Waste_percent": w_oth,
                "Collection_Frequency_per_week": w_coll,
                "Recycling_Rate_percent": w_rec,
                "month": d.month,
                "dayofweek": d.weekday()
                # FIX 3: Area_ID, Household_Size, Per_Capita_Income,
                #         Urban_Rural_Type, Humidity_percent REMOVED
                # FIX 1: dayofyear REMOVED
            }
            with st.spinner("Running RandomForest · GradientBoosting · XGBoost…"):  # FIX 6
                resp = api_post("/predict/waste", payload)
            if "error" in resp:
                st.error(resp["error"])
            else:
                pred  = resp["prediction"]
                waste = pred["waste_generated_tons"]
                lo    = pred["lower_bound"]
                hi    = pred["upper_bound"]
                render_animated_counter("Predicted Waste Generation", waste, "Tonnes / Day", f"{lo:.2f} t", f"{hi:.2f} t")
                st.markdown("<br>", unsafe_allow_html=True)
                total = w_org + w_pla + w_pap + w_oth + 1e-6
                comp_df = pd.DataFrame({"Category":["Organic","Plastic","Paper","Other"],
                    "Tons":[waste*w_org/total, waste*w_pla/total, waste*w_pap/total, waste*w_oth/total]})
                st.bar_chart(comp_df.set_index("Category"), color="#00ff50", height=200)


# ══════════════════════════════════════════════════════════════
# TAB 3 — ROUTE OPTIMIZATION
# ══════════════════════════════════════════════════════════════
with tab3:
    rv1, rv2, rv3 = st.columns(3)
    v_cap  = rv1.number_input("Capacity kg",        1000, 10000, 5000, step=500)
    v_load = rv2.number_input("Current Load kg",    0, 10000, 0, step=100)
    v_fuel = rv3.number_input("Fuel km/L",          1.0, 20.0, 5.0, step=0.5)

    if "route_stops" not in st.session_state:
        st.session_state.route_stops = [
            {"id":"DEPOT",  "name":"Municipal Depot",       "lat":17.385,"lon":78.487,"waste_kg":0,  "fill":0, "traffic":"Low",   "road":"Highway",  "cond":"Good"},
            {"id":"ZONE-A", "name":"Zone A — Jubilee Hills","lat":17.431,"lon":78.409,"waste_kg":620,"fill":85,"traffic":"High",  "road":"Main_Road","cond":"Good"},
            {"id":"ZONE-B", "name":"Zone B — Banjara Hills","lat":17.415,"lon":78.441,"waste_kg":480,"fill":72,"traffic":"Medium","road":"Main_Road","cond":"Average"},
            {"id":"ZONE-C", "name":"Zone C — Madhapur",    "lat":17.449,"lon":78.390,"waste_kg":730,"fill":91,"traffic":"High",  "road":"Highway",  "cond":"Good"},
            {"id":"ZONE-D", "name":"Zone D — Gachibowli",  "lat":17.440,"lon":78.347,"waste_kg":290,"fill":58,"traffic":"Medium","road":"Highway",  "cond":"Good"},
            {"id":"ZONE-E", "name":"Zone E — Kondapur",    "lat":17.471,"lon":78.356,"waste_kg":410,"fill":68,"traffic":"Low",   "road":"Residential","cond":"Average"},
            {"id":"PLANT",  "name":"Recycling Plant",      "lat":17.360,"lon":78.480,"waste_kg":0,  "fill":0, "traffic":"Low",   "road":"Highway",  "cond":"Good"},
        ]

    # 3D GLOBE — show stop locations before optimization
    st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.6rem;letter-spacing:.15em;color:rgba(0,255,80,.4);margin-bottom:8px">3D LOCATION GLOBE — DRAG TO ROTATE</div>', unsafe_allow_html=True)
    render_3d_globe(st.session_state.route_stops)

    st.markdown("<br>", unsafe_allow_html=True)
    stop_df = pd.DataFrame(st.session_state.route_stops)
    edited  = st.data_editor(
        stop_df[["id","name","lat","lon","waste_kg","fill","traffic","road","cond"]],
        use_container_width=True, num_rows="dynamic",
        column_config={
            "id":       st.column_config.TextColumn("Stop ID",    width="small"),
            "name":     st.column_config.TextColumn("Name"),
            "lat":      st.column_config.NumberColumn("Latitude", format="%.4f"),
            "lon":      st.column_config.NumberColumn("Longitude",format="%.4f"),
            "waste_kg": st.column_config.NumberColumn("Waste kg", min_value=0),
            "fill":     st.column_config.NumberColumn("Fill %",   min_value=0, max_value=100),
            "traffic":  st.column_config.SelectboxColumn("Traffic",   options=["Low","Medium","High"]),
            "road":     st.column_config.SelectboxColumn("Road",      options=["Residential","Main_Road","Highway"]),
            "cond":     st.column_config.SelectboxColumn("Condition", options=["Poor","Average","Good"]),
        }, key="rt_editor"
    )

    optimize_btn = st.button("▸ Run 2-Opt + ML Route Optimization", use_container_width=True)

    if optimize_btn:
        stops_payload = []
        for _, row in edited.iterrows():
            stops_payload.append({
                "id": str(row["id"]), "name": str(row["name"]),
                "lat": float(row["lat"]), "lon": float(row["lon"]),
                "waste_kg": float(row.get("waste_kg",400)),
                "fill_percent": float(row.get("fill",65)),
                "traffic": str(row.get("traffic","Medium")),
                "road_type_str": str(row.get("road","Main_Road")),
                "road_condition": str(row.get("cond","Average")),
                "one_way": 0, "toll": 0,
                "population_density": 5000, "collection_freq": 3
            })

        with st.spinner("Running greedy NN → 2-opt → ML cost scoring…"):
            resp = api_post("/optimize", {
                "stops": stops_payload,
                "vehicle": {"capacity_kg": v_cap, "current_load_kg": v_load, "fuel_km_per_l": v_fuel},
                "depot_index": 0
            })

        if "error" in resp:
            st.error(resp["error"])
        else:
            opt = resp["optimization"]
            k1,k2,k3,k4 = st.columns(4)
            # FIX 7: .get() with fallbacks for all keys
            k1.metric("Total Distance",    f"{opt.get('total_distance_km', 0)} km")
            k2.metric("Est. Travel Time",  f"{opt.get('total_time_min', 0):.0f} min")
            k3.metric("2-opt Improvement", f"{opt.get('improvement_percent', opt.get('saved_percent',0)):.1f}%")
            k4.metric("Stops",             str(opt.get('num_stops', len(stops_payload))))

            col_seq, col_map = st.columns([1, 1.4])

            with col_seq:
                ordered = opt.get("ordered_stops", [])  # FIX 7
                for i, stop in enumerate(ordered):
                    fill     = stop.get("fill_percent", stop.get("fill",0))
                    is_depot = i == 0 or i == len(ordered)-1
                    fill_color = "#00ff50" if is_depot else ("#ff4444" if fill>=85 else ("#ffaa00" if fill>=70 else "#3a7a3a"))
                    border_cls = "depot" if is_depot else ("high-fill" if fill>=85 else ("med-fill" if fill>=70 else ""))
                    st.markdown(f"""<div class="eco-route-stop {border_cls}">
                      <span style="font-family:Orbitron,sans-serif;font-weight:700;color:#00ff50;min-width:1.5rem">{i+1}</span>
                      <div style="flex:1">
                        <div style="font-family:Rajdhani,sans-serif;font-size:.9rem;color:#e0ffe0">{stop['name']}</div>
                        <div style="font-family:Share Tech Mono,monospace;font-size:.62rem;color:rgba(0,255,80,.25)">{stop['lat']:.4f}, {stop['lon']:.4f}</div>
                      </div>
                      <span style="font-family:Orbitron,sans-serif;font-weight:600;font-size:.8rem;color:{fill_color}">{fill:.0f}%</span>
                    </div>""", unsafe_allow_html=True)

            with col_map:
                ordered = opt.get("ordered_stops", [])  # FIX 7
                if ordered:
                    clat = sum(s["lat"] for s in ordered)/len(ordered)
                    clon = sum(s["lon"] for s in ordered)/len(ordered)
                    m = folium.Map(location=[clat,clon], zoom_start=13, tiles="CartoDB dark_matter")
                    coords = [[s["lat"],s["lon"]] for s in ordered]
                    coords.append(coords[0])
                    folium.PolyLine(coords, color="#00ff50", weight=3, opacity=0.8, dash_array="6 4").add_to(m)
                    for i, stop in enumerate(ordered):
                        fill = stop.get("fill_percent", stop.get("fill",0))
                        is_depot = i==0 or i==len(ordered)-1
                        color = "green" if is_depot else ("red" if fill>=85 else ("orange" if fill>=70 else "blue"))
                        folium.Marker(
                            location=[stop["lat"],stop["lon"]],
                            popup=folium.Popup(f"<b>Stop #{i+1} — {stop['name']}</b><br>Fill: {fill:.0f}%", max_width=220),
                            tooltip=f"{i+1}. {stop['name']} ({fill:.0f}%)",
                            icon=folium.Icon(color=color, icon="info-sign", prefix="glyphicon")
                        ).add_to(m)
                    st_folium(m, width=520, height=380, returned_objects=[])