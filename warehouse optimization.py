import streamlit as st
import pulp
import matplotlib.pyplot as plt

st.title("🚚 Generalized Supply Chain Optimizer")
st.write("Robust Distribution Network Optimization Model")

# --- FIXED COSTS ---
cost_E1_A1 = 700
cost_E1_KD = 300
cost_E2_KD = 500
cost_E2_A2 = 1000
cost_KD_A1 = 200
cost_KD_A2 = 400
penalty_shortage = 5000  # Large Cost if demand cannot be covered

# --- GUI CONTROLS ---
st.sidebar.header("⚙️ Network Parameters")

st.sidebar.subheader("Factories (Maximum Production Capacity)")
cap_E1 = st.sidebar.slider("Capacity Ε1", 0, 200, 80)
cap_E2 = st.sidebar.slider("Capacity Ε2", 0, 200, 70)

st.sidebar.subheader("Warehouses (Demand)")
demand_A1 = st.sidebar.slider("Demand Α1", 0, 200, 60)
demand_A2 = st.sidebar.slider("Demand Α2", 0, 200, 90)

st.sidebar.subheader("Transportation Limitations")
truck_cap = st.sidebar.slider("Maximum Capacity of Trucks (ΚΔ)", 10, 150, 50)

# --- ΝΕΟ: ΔΥΝΑΜΙΚΑ ΟΡΙΑ ΜΕΤΑΒΛΗΤΩΝ ΑΠΟ ΤΟΝ ΧΡΗΣΤΗ ---
st.sidebar.header("🛑 Custom Variable Bounds")
st.sidebar.write("Set the absolute Min and Max flow allowed for routes:")

# Δημιουργία drop-down ή sliders/inputs για γενικά όρια ροής
flow_min = st.sidebar.number_input("Minimum Flow (All Routes)", min_value=0, value=0, step=5)
flow_max = st.sidebar.number_input("Maximum Flow (All Routes)", min_value=0, value=150, step=5)

# --- PULP OPTIMIZATION MODEL ---
prob = pulp.LpProblem("Robust_Supply_Chain", pulp.LpMinimize)

# Μεταβλητές Ροής με τα όρια που έθεσε ο χρήστης
# Σημείωση: Για τις διαδρομές μέσω ΚΔ, το μέγιστο όριο περιορίζεται είτε από το flow_max του χρήστη είτε από το truck_cap (το μικρότερο εκ των δύο)
max_truck_route = min(flow_max, truck_cap)

x1 = pulp.LpVariable('x1_E1_A1', lowBound=flow_min, upBound=flow_max)
x2 = pulp.LpVariable('x2_E1_KD', lowBound=flow_min, upBound=max_truck_route)
x3 = pulp.LpVariable('x3_E2_KD', lowBound=flow_min, upBound=max_truck_route)
x4 = pulp.LpVariable('x4_E2_A2', lowBound=flow_min, upBound=max_truck_route)
x5 = pulp.LpVariable('x5_KD_A1', lowBound=flow_min, upBound=max_truck_route)
x6 = pulp.LpVariable('x6_KD_A2', lowBound=flow_min, upBound=max_truck_route)

# Shortage Variables (Shortage) so that the model doesn't crash
shortage_A1 = pulp.LpVariable('shortage_A1', lowBound=0)
shortage_A2 = pulp.LpVariable('shortage_A2', lowBound=0)

# Objective Function: Transportation Costs + Shortage Penalties
prob += (cost_E1_A1*x1 + cost_E1_KD*x2 + cost_E2_KD*x3 + cost_E2_A2*x4 + 
         cost_KD_A1*x5 + cost_KD_A2*x6 + penalty_shortage*shortage_A1 + penalty_shortage*shortage_A2), "Total_Cost"

# --- GENERALIZED CONSTRAINTS ---
prob += x1 + x2 <= cap_E1          # Ε1 Output cannot exceed its production
prob += x3 + x4 <= cap_E2          # Ε2 Output cannot exceed its production

# Ροή + Έλλειψη πρέπει να καλύπτουν τη ζήτηση
prob += x1 + x5 + shortage_A1 >= demand_A1  
prob += x4 + x6 + shortage_A2 >= demand_A2  

# Απόλυτο Ισοζύγιο στο Κέντρο Διανομής (Ό,τι μπαίνει, βγαίνει)
prob += x2 + x3 == x5 + x6         

# Επίλυση
prob.solve(pulp.PULP_CBC_CMD(msg=False))

# --- ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
# Έλεγχος αν το μοντέλο βρήκε λύση (π.χ. αν ο χρήστης έβαλε πολύ υψηλό Minimum Flow, ίσως είναι Infeasible)
if pulp.LpStatus[prob.status] == "Infeasible":
    st.error("❌ No Feasible Solution! The minimum bounds you set are too high for the network capacity.")
else:
    total_shortage = shortage_A1.varValue + shortage_A2.varValue

    if total_shortage > 0:
        st.warning(f"⚠️ Warning: Production or Transport is not sufficient! Total Shortages: {total_shortage} Units.")
    else:
        st.success("🎯 Optimal Solution: Total Demand has been covered with the minimum cost!")

    # Υπολογισμός πραγματικού κόστους μεταφοράς
    real_transport_cost = (cost_E1_A1*x1.varValue + cost_E1_KD*x2.varValue + 
                           cost_E2_KD*x3.varValue + cost_E2_A2*x4.varValue + 
                           cost_KD_A1*x5.varValue + cost_KD_A2*x6.varValue)

    st.metric(label="📊 Actual Cost of Transportation (€)", value=f"{real_transport_cost:,.2f} €")

    # Στατιστικά Στοιχεία
    col_data1, col_data2 = st.columns(2)
    col_data1.metric("Total Production Capacity", f"{cap_E1 + cap_E2} Units")
    col_data2.metric("Total Demand", f"{demand_A1 + demand_A2} Units")

    # Πίνακας Ροών
    st.subheader("📦 Route Allocation")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🚂 Rail (Direct)**")
        st.write(f"Ε1 → Α1: {x1.varValue} Units")
        st.write(f"Ε2 → Α2: {x4.varValue} Units")
    with c2:
        st.markdown("**🚚 Trucks (Through ΚΔ)**")
        st.write(f"Ε1 → ΚΔ: {x2.varValue} Units | Ε2 → ΚΔ: {x3.varValue} Units")
        st.write(f"ΚΔ → Α1: {x5.varValue} Units | ΚΔ → Α2: {x6.varValue} Units")

    if total_shortage > 0:
        st.subheader("🚨 Shortages Report")
        st.write(f"Shortages in Warehouse Α1: {shortage_A1.varValue} Units")
        st.write(f"Shortages in Warehouse Α2: {shortage_A2.varValue} Units")
