import streamlit as st
import pulp
import matplotlib.pyplot as plt

st.title("🚚 Generalized Supply Chain Optimizer")
st.write("Ανθεκτικό μοντέλο βελτιστοποίησης δικτύου διανομής (P&G Framework)")

# --- ΣΤΑΘΕΡΑ ΚΟΣΤΗ (Μπορούν να γίνουν και αυτά sliders) ---
cost_E1_A1 = 700
cost_E1_KD = 300
cost_E2_KD = 500
cost_E2_A2 = 1000
cost_KD_A1 = 200
cost_KD_A2 = 400
penalty_shortage = 5000  # Μεγάλο κόστος αν δεν μπορούμε να καλύψουμε τη ζήτηση

# --- GUI CONTROLS ---
st.sidebar.header("⚙️ Παράμετροι Δικτύου")

st.sidebar.subheader("Εργοστάσια (Μέγιστη Παραγωγή)")
cap_E1 = st.sidebar.slider("Δυναμικότητα Ε1", 0, 200, 80)
cap_E2 = st.sidebar.slider("Δυναμικότητα Ε2", 0, 200, 70)

st.sidebar.subheader("Αποθήκες (Ζήτηση)")
demand_A1 = st.sidebar.slider("Ζήτηση Α1", 0, 200, 60)
demand_A2 = st.sidebar.slider("Ζήτηση Α2", 0, 200, 90)

st.sidebar.subheader("Περιορισμοί Μεταφοράς")
truck_cap = st.sidebar.slider("Μέγιστη Χωρητικότητα Φορτηγών (ΚΔ)", 10, 150, 50)

# --- PULP OPTIMIZATION MODEL ---
prob = pulp.LpProblem("Robust_Supply_Chain", pulp.LpMinimize)

# Μεταβλητές Ροής
x1 = pulp.LpVariable('x1_E1_A1', lowBound=0)
x2 = pulp.LpVariable('x2_E1_KD', lowBound=0, upBound=truck_cap)
x3 = pulp.LpVariable('x3_E2_KD', lowBound=0, upBound=truck_cap)
x4 = pulp.LpVariable('x4_E2_A2', lowBound=0, upBound=truck_cap)
x5 = pulp.LpVariable('x5_KD_A1', lowBound=0, upBound=truck_cap)
x6 = pulp.LpVariable('x6_KD_A2', lowBound=0, upBound=truck_cap)

# Μεταβλητές Έλλειψης (Shortage) για να μην κρασάρει ποτέ το μοντέλο
shortage_A1 = pulp.LpVariable('shortage_A1', lowBound=0)
shortage_A2 = pulp.LpVariable('shortage_A2', lowBound=0)

# Αντικειμενική Συνάρτηση: Κόστη Μεταφοράς + Πέναλτι Ελλείψεων
prob += (cost_E1_A1*x1 + cost_E1_KD*x2 + cost_E2_KD*x3 + cost_E2_A2*x4 + 
         cost_KD_A1*x5 + cost_KD_A2*x6 + penalty_shortage*shortage_A1 + penalty_shortage*shortage_A2), "Total_Cost"

# --- ΓΕΝΙΚΕΥΜΕΝΟΙ ΠΕΡΙΟΡΙΣΜΟΙ ---
prob += x1 + x2 <= cap_E1          # Η εκροή του Ε1 δεν μπορεί να ξεπερνά την παραγωγή του
prob += x3 + x4 <= cap_E2          # Η εκροή του Ε2 δεν μπορεί να ξεπερνά την παραγωγή του

# Ροή + Έλλειψη πρέπει να καλύπτουν τη ζήτηση
prob += x1 + x5 + shortage_A1 >= demand_A1  
prob += x4 + x6 + shortage_A2 >= demand_A2  

# Απόλυτο Ισοζύγιο στο Κέντρο Διανομής (Ό,τι μπαίνει, βγαίνει)
prob += x2 + x3 == x5 + x6         

# Επίλυση
prob.solve(pulp.PULP_CBC_CMD(msg=False))

# --- ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---
total_shortage = shortage_A1.varValue + shortage_A2.varValue

if total_shortage > 0:
    st.warning(f"⚠️ Προειδοποίηση: Η παραγωγή δεν επαρκεί! Συνολική έλλειψη: {total_shortage} τεμάχια.")
else:
    st.success("🎯 Ιδανική Λύση: Όλη η ζήτηση καλύφθηκε με το ελάχιστο κόστος!")

# Υπολογισμός πραγματικού κόστους μεταφοράς (χωρίς το τεχνητό πέναλτι)
real_transport_cost = (cost_E1_A1*x1.varValue + cost_E1_KD*x2.varValue + 
                       cost_E2_KD*x3.varValue + cost_E2_A2*x4.varValue + 
                       cost_KD_A1*x5.varValue + cost_KD_A2*x6.varValue)

st.metric(label="📊 Πραγματικό Κόστος Μεταφοράς (€)", value=f"{real_transport_cost:,.2f} €")

# Στατιστικά Στοιχεία
col_data1, col_data2 = st.columns(2)
col_data1.metric("Συνολική Παραγωγή", f"{cap_E1 + cap_E2} μονάδες")
col_data2.metric("Συνολική Ζήτηση", f"{demand_A1 + demand_A2} μονάδες")

# Πίνακας Ροών
st.subheader("📦 Κατανομή Δρομολογίων")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**🚂 Σιδηρόδρομος (Απευθείας)**")
    st.write(f"Ε1 → Α1: {x1.varValue} τμχ")
    st.write(f"Ε2 → Α2: {x4.varValue} τμχ")
with c2:
    st.markdown("**🚚 Φορτηγά (Μέσω ΚΔ)**")
    st.write(f"Ε1 → ΚΔ: {x2.varValue} τμχ | Ε2 → ΚΔ: {x3.varValue} τμχ")
    st.write(f"ΚΔ → Α1: {x5.varValue} τμχ | ΚΔ → Α2: {x6.varValue} τμχ")

if total_shortage > 0:
    st.subheader("🚨 Αναφορές Ελλείψεων")
    st.write(f"Έλλειψη στην Αποθήκη Α1: {shortage_A1.varValue} τεμάχια")
    st.write(f"Έλλειψη στην Αποθήκη Α2: {shortage_A2.varValue} τεμάχια")
