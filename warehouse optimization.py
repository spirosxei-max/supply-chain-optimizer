import streamlit as st
import pulp
import matplotlib.pyplot as plt

st.set_page_config(layout="wide") # Φαρδύ layout για να χωράνε οι στήλες

st.title("🚚 Generalized Supply Chain Optimizer")
st.write("Robust Distribution Network Optimization Model")

# --- FIXED COSTS ---
cost_E1_A1 = 700
cost_E1_DC = 300
cost_E2_DC = 500
cost_E2_A2 = 1000
cost_DC_A1 = 200
cost_DC_A2 = 400
penalty_shortage = 5000  # Large Cost if demand cannot be covered

# --- GUI CONTROLS (Στο κεντρικό πάνελ για σωστή στοίχιση) ---
st.header("⚙️ Network Parameters & Dynamic Ranges")
st.write("Set the Minimum, Current Value, and Maximum for each parameter:")

# --- FACTORIES BOUNDS & SLIDERS ---
st.subheader("🏭 Factories (Production Capacity)")

col1_min, col1_slide, col1_max = st.columns([1, 2, 1])
with col1_min:
    min_E1 = st.number_input("Min E1", min_value=0, value=0, key="min_e1")
with col1_max:
    max_E1 = st.number_input("Max E1", min_value=min_E1, value=200, key="max_e1")
with col1_slide:
    # Διασφάλιση ότι η προεπιλεγμένη τιμή είναι εντός των ορίων του χρήστη
    val_E1 = min(max(80, min_E1), max_E1)
    cap_E1 = st.slider("Capacity Ε1", min_value=min_E1, max_value=max_E1, value=val_E1)

col2_min, col2_slide, col2_max = st.columns([1, 2, 1])
with col2_min:
    min_E2 = st.number_input("Min E2", min_value=0, value=0, key="min_e2")
with col2_max:
    max_E2 = st.number_input("Max E2", min_value=min_E2, value=200, key="max_e2")
with col2_slide:
    val_E2 = min(max(70, min_E2), max_E2)
    cap_E2 = st.slider("Capacity Ε2", min_value=min_E2, max_value=max_E2, value=val_E2)


# --- WAREHOUSES BOUNDS & SLIDERS ---
st.subheader("📦 Warehouses (Demand)")

col3_min, col3_slide, col3_max = st.columns([1, 2, 1])
with col3_min:
    min_A1 = st.number_input("Min A1", min_value=0, value=0, key="min_a1")
with col3_max:
    max_A1 = st.number_input("Max A1", min_value=min_A1, value=200, key="max_a1")
with col3_slide:
    val_A1 = min(max(60, min_A1), max_A1)
    demand_A1 = st.slider("Demand Α1", min_value=min_A1, max_value=max_A1, value=val_A1)

col4_min, col4_slide, col4_max = st.columns([1, 2, 1])
with col4_min:
    min_A2 = st.number_input("Min A2", min_value=0, value=0, key="min_a2")
with col4_max:
    max_A2 = st.number_input("Max A2", min_value=min_A2, value=200, key="max_a2")
with col4_slide:
    val_A2 = min(max(90, min_A2), max_A2)
    demand_A2 = st.slider("Demand Α2", min_value=min_A2, max_value=max_A2, value=val_A2)


# --- TRUCK BOUNDS & SLIDERS ---
st.subheader("🚛 Transportation Limitations")

col5_min, col5_slide, col5_max = st.columns([1, 2, 1])
with col5_min:
    min_truck = st.number_input("Min Truck", min_value=0, value=10, key="min_tr")
with col5_max:
    max_truck = st.number_input("Max Truck", min_value=min_truck, value=150, key="max_tr")
with col5_slide:
    val_truck = min(max(50, min_truck), max_truck)
    truck_cap = st.slider("Maximum Capacity of Trucks (Distribution Center)", min_value=min_truck, max_value=max_truck, value=val_truck)

st.markdown("---")

# --- PULP OPTIMIZATION MODEL ---
prob = pulp.LpProblem("Robust_Supply_Chain", pulp.LpMinimize)

# Μεταβλητές Ροής
x1 = pulp.LpVariable('x1_E1_A1', lowBound=0)
x2 = pulp.LpVariable('x2_E1_DC', lowBound=0, upBound=truck_cap)
x3 = pulp.LpVariable('x3_E2_DC', lowBound=0, upBound=truck_cap)
x4 = pulp.LpVariable('x4_E2_A2', lowBound=0, upBound=truck_cap)
x5 = pulp.LpVariable('x5_DC_A1', lowBound=0, upBound=truck_cap)
x6 = pulp.LpVariable('x6_DC_A2', lowBound=0, upBound=truck_cap)

# Shortage Variables
shortage_A1 = pulp.LpVariable('shortage_A1', lowBound=0)
shortage_A2 = pulp.LpVariable('shortage_A2', lowBound=0)

# Objective Function
prob += (cost_E1_A1*x1 + cost_E1_DC*x2 + cost_E2_DC*x3 + cost_E2_A2*x4 + 
         cost_DC_A1*x5 + cost_DC_A2*x6 + penalty_shortage*shortage_A1 + penalty_shortage*shortage_A2), "Total_Cost"

# Constraints
prob += x1 + x2 <= cap_E1          
prob += x3 + x4 <= cap_E2          
prob += x1 + x5 + shortage_A1 >= demand_A1  
prob += x4 + x6 + shortage_A2 >= demand_A2  
prob += x2 + x3 == x5 + x6         

# Επίλυση
prob.solve(pulp.PULP_CBC_CMD(msg=False))

# --- ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
total_shortage = shortage_A1.varValue + shortage_A2.varValue

if total_shortage > 0:
    st.warning(f"⚠️ Warning: Production is not sufficient! Total Shortages: {total_shortage} Units.")
else:
    st.success("🎯 Optimal Solution: Total Demand has been covered with the minimum cost!")

real_transport_cost = (cost_E1_A1*x1.varValue + cost_E1_DC*x2.varValue + 
                       cost_E2_DC*x3.varValue + cost_E2_A2*x4.varValue + 
                       cost_DC_A1*x5.varValue + cost_DC_A2*x6.varValue)

st.metric(label="📊 Actual Cost of Transportation (€)", value=f"{real_transport_cost:,.2f} €")

col_data1, col_data2 = st.columns(2)
col_data1.metric("Total Production Chosen", f"{cap_E1 + cap_E2} Units")
col_data2.metric("Total Demand Chosen", f"{demand_A1 + demand_A2} Units")

st.subheader("📦 Route Allocation")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**🚂 Rail (Direct)**")
    st.write(f"Ε1 → Α1: {x1.varValue} Units")
    st.write(f"Ε2 → Α2: {x4.varValue} Units")
with c2:
    st.markdown("**🚚 Trucks (Through DC)**")
    st.write(f"Ε1 → DC: {x2.varValue} Units | Ε2 → DC: {x3.varValue} Units")
    st.write(f"DC → Α1: {x5.varValue} Units | DC → Α2: {x6.varValue} Units")

if total_shortage > 0:
    st.subheader("🚨 Shortages Report")
    st.write(f"Shortages in Warehouse Α1: {shortage_A1.varValue} Units")
    st.write(f"Shortages in Warehouse Α2: {shortage_A2.varValue} Units")
