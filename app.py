import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Horário de Trabalho - Scheduler",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .schedule-table {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def create_scheduling_model(num_days, num_workers, required_staff_weekday, required_staff_weekend):
    """Create and solve the scheduling model"""
    model = cp_model.CpModel()
    
    # Sets
    days = range(num_days)
    workers = range(num_workers)
    shifts = ['manha', 'central', 'tarde', 'noite']
    weekday_shifts = ['manha', 'central', 'tarde', 'noite']
    weekend_shifts = ['manha', 'tarde', 'noite']
    
    # Define shifts per day type
    shifts_by_day_type = {}
    for d in days:
        if d % 7 == 5 or d % 7 == 6:  # Saturday or Sunday
            shifts_by_day_type[d] = weekend_shifts
        else:  # Monday to Friday
            shifts_by_day_type[d] = weekday_shifts
    
    # Decision Variables
    x = {}
    for w in workers:
        for d in days:
            for s in shifts_by_day_type[d]:
                x[(w, d, s)] = model.NewBoolVar(f'x_{w}_{d}_{s}')
    
    # Constraint 1: Unique People Per Shift
    for w in workers:
        for d in days:
            model.AddAtMostOne([x[(w, d, s)] for s in shifts_by_day_type[d]])
    
    # Constraint 2: Required Staff Per Shift
    for d in days:
        for s in shifts_by_day_type[d]:
            if d % 7 == 5 or d % 7 == 6:  # Weekend
                model.Add(sum(x[(w, d, s)] for w in workers) == required_staff_weekend[s])
            else:  # Weekday
                model.Add(sum(x[(w, d, s)] for w in workers) == required_staff_weekday[s])
    
    # Constraint 3: No more than 5 days work per week (rolling window)
    for w in workers:
        for start_day in range(num_days - 6):
            working_days_in_window = []
            for d in range(start_day, start_day + 7):
                works_on_day = model.NewBoolVar(f'works_{w}_{d}')
                model.AddBoolOr([x[(w, d, s)] for s in shifts_by_day_type[d]]).OnlyEnforceIf(works_on_day)
                model.Add(sum(x[(w, d, s)] for s in shifts_by_day_type[d]) == 0).OnlyEnforceIf(works_on_day.Not())
                working_days_in_window.append(works_on_day)
            model.Add(sum(working_days_in_window) <= 5)
    
    # Solve the model
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)
    
    return solver, status, x, shifts_by_day_type, days, workers

def create_schedule_dataframe(solver, x, shifts_by_day_type, days, workers):
    """Create a pandas DataFrame with the schedule"""
    schedule_data = []
    
    for d in days:
        for s in shifts_by_day_type[d]:
            assigned_workers = []
            for w in workers:
                if solver.Value(x[(w, d, s)]) == 1:
                    assigned_workers.append(w)
            
            # Calculate date
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            current_date = start_date + timedelta(days=d)
            
            schedule_data.append({
                'Date': current_date,
                'Day': current_date.strftime('%A'),
                'Day_Num': d,
                'Shift': s,
                'Workers': assigned_workers,
                'Worker_Count': len(assigned_workers),
                'Is_Weekend': d % 7 >= 5
            })
    
    return pd.DataFrame(schedule_data)

def create_worker_summary(solver, x, shifts_by_day_type, days, workers):
    """Create a summary of worker assignments"""
    worker_data = []
    
    for w in workers:
        total_shifts = 0
        weekday_shifts = 0
        weekend_shifts = 0
        shift_counts = {'manha': 0, 'central': 0, 'tarde': 0, 'noite': 0}
        
        for d in days:
            for s in shifts_by_day_type[d]:
                if solver.Value(x[(w, d, s)]) == 1:
                    total_shifts += 1
                    shift_counts[s] += 1
                    if d % 7 >= 5:  # Weekend
                        weekend_shifts += 1
                    else:
                        weekday_shifts += 1
        
        worker_data.append({
            'Worker_ID': w,
            'Total_Shifts': total_shifts,
            'Weekday_Shifts': weekday_shifts,
            'Weekend_Shifts': weekend_shifts,
            'Manha_Shifts': shift_counts['manha'],
            'Central_Shifts': shift_counts['central'],
            'Tarde_Shifts': shift_counts['tarde'],
            'Noite_Shifts': shift_counts['noite']
        })
    
    return pd.DataFrame(worker_data)

def main():
    # Header
    st.markdown('<h1 class="main-header">📅 Sistema de Horários de Trabalho</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configurações")
    
    # Input parameters
    num_days = st.sidebar.slider("Período (dias)", 7, 30, 14, help="Número de dias para planejar")
    num_workers = st.sidebar.slider("Número de Funcionários", 15, 30, 23, help="Total de funcionários disponíveis")
    
    st.sidebar.subheader("📊 Staff Necessário - Dias Úteis")
    manha_weekday = st.sidebar.number_input("Manhã", 1, 10, 6, key="manha_wd")
    central_weekday = st.sidebar.number_input("Central", 1, 5, 2, key="central_wd")
    tarde_weekday = st.sidebar.number_input("Tarde", 1, 10, 6, key="tarde_wd")
    noite_weekday = st.sidebar.number_input("Noite", 1, 8, 3, key="noite_wd")
    
    st.sidebar.subheader("📊 Staff Necessário - Fins de Semana")
    manha_weekend = st.sidebar.number_input("Manhã", 1, 8, 3, key="manha_we")
    tarde_weekend = st.sidebar.number_input("Tarde", 1, 8, 3, key="tarde_we")
    noite_weekend = st.sidebar.number_input("Noite", 1, 8, 3, key="noite_we")
    
    required_staff_weekday = {
        'manha': manha_weekday,
        'central': central_weekday,
        'tarde': tarde_weekday,
        'noite': noite_weekday
    }
    
    required_staff_weekend = {
        'manha': manha_weekend,
        'tarde': tarde_weekend,
        'noite': noite_weekend
    }
    
    # Solve button
    if st.sidebar.button("🚀 Gerar Horário", type="primary"):
        with st.spinner("Calculando horário..."):
            try:
                solver, status, x, shifts_by_day_type, days, workers = create_scheduling_model(
                    num_days, num_workers, required_staff_weekday, required_staff_weekend
                )
                
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    st.success(f"✅ Horário gerado com sucesso! Status: {solver.StatusName(status)}")
                    
                    # Create dataframes
                    schedule_df = create_schedule_dataframe(solver, x, shifts_by_day_type, days, workers)
                    worker_summary = create_worker_summary(solver, x, shifts_by_day_type, days, workers)
                    
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total de Dias", num_days)
                    
                    with col2:
                        st.metric("Funcionários", num_workers)
                    
                    with col3:
                        total_shifts = len(schedule_df)
                        st.metric("Total de Turnos", total_shifts)
                    
                    with col4:
                        avg_shifts_per_worker = worker_summary['Total_Shifts'].mean()
                        st.metric("Média de Turnos/Funcionário", f"{avg_shifts_per_worker:.1f}")
                    
                    # Tabs for different views
                    tab1, tab2, tab3, tab4 = st.tabs(["📅 Horário Completo", "👥 Resumo por Funcionário", "📊 Estatísticas", "🔍 Análise Detalhada"])
                    
                    with tab1:
                        st.subheader("📅 Horário Completo")
                        
                        # Filter options
                        col1, col2 = st.columns(2)
                        with col1:
                            selected_shift = st.selectbox("Filtrar por Turno", ["Todos"] + list(schedule_df['Shift'].unique()))
                        with col2:
                            show_weekend_only = st.checkbox("Apenas Fins de Semana")
                        
                        # Apply filters
                        filtered_df = schedule_df.copy()
                        if selected_shift != "Todos":
                            filtered_df = filtered_df[filtered_df['Shift'] == selected_shift]
                        if show_weekend_only:
                            filtered_df = filtered_df[filtered_df['Is_Weekend'] == True]
                        
                        # Display schedule
                        for _, row in filtered_df.iterrows():
                            with st.expander(f"{row['Date'].strftime('%d/%m/%Y')} - {row['Day']} - Turno: {row['Shift'].title()}"):
                                st.write(f"**Funcionários:** {row['Workers']}")
                                st.write(f"**Quantidade:** {row['Worker_Count']}")
                    
                    with tab2:
                        st.subheader("👥 Resumo por Funcionário")
                        
                        # Worker summary table
                        st.dataframe(worker_summary, use_container_width=True)
                        
                        # Worker distribution chart
                        fig = px.bar(worker_summary, x='Worker_ID', y='Total_Shifts',
                                   title="Distribuição de Turnos por Funcionário",
                                   labels={'Worker_ID': 'Funcionário', 'Total_Shifts': 'Total de Turnos'})
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab3:
                        st.subheader("📊 Estatísticas")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Shift distribution
                            shift_counts = schedule_df['Shift'].value_counts()
                            fig = px.pie(values=shift_counts.values, names=shift_counts.index,
                                       title="Distribuição de Turnos")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            # Day of week distribution
                            day_counts = schedule_df['Day'].value_counts()
                            fig = px.bar(x=day_counts.index, y=day_counts.values,
                                       title="Distribuição por Dia da Semana",
                                       labels={'x': 'Dia', 'y': 'Quantidade de Turnos'})
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab4:
                        st.subheader("🔍 Análise Detalhada")
                        
                        # Worker shift preferences
                        shift_preferences = worker_summary[['Manha_Shifts', 'Central_Shifts', 'Tarde_Shifts', 'Noite_Shifts']].sum()
                        fig = px.bar(x=shift_preferences.index, y=shift_preferences.values,
                                   title="Total de Turnos por Tipo",
                                   labels={'x': 'Tipo de Turno', 'y': 'Total de Turnos'})
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Weekend vs Weekday distribution
                        weekend_weekday = worker_summary[['Weekday_Shifts', 'Weekend_Shifts']].sum()
                        fig = px.pie(values=weekend_weekday.values, names=weekend_weekday.index,
                                   title="Distribuição Dias Úteis vs Fins de Semana")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Download options
                    st.subheader("💾 Download dos Dados")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_schedule = schedule_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Horário (CSV)",
                            data=csv_schedule,
                            file_name=f"horario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        csv_workers = worker_summary.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Resumo Funcionários (CSV)",
                            data=csv_workers,
                            file_name=f"resumo_funcionarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Solver statistics
                    with st.expander("📈 Estatísticas do Solver"):
                        st.write(f"**Conflitos:** {solver.NumConflicts()}")
                        st.write(f"**Branches:** {solver.NumBranches()}")
                        st.write(f"**Tempo de Execução:** {solver.WallTime():.2f}s")
                
                else:
                    st.error(f"❌ Não foi possível encontrar uma solução. Status: {solver.status_name(status)}")
                    
            except Exception as e:
                st.error(f"❌ Erro ao gerar horário: {str(e)}")
    
    # Instructions
    else:
        st.info("👈 Use a barra lateral para configurar os parâmetros e clique em 'Gerar Horário' para começar.")
        
        # Show default configuration
        st.subheader("📋 Configuração Padrão")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Dias Úteis:**")
            st.write("- Manhã: 6 funcionários")
            st.write("- Central: 2 funcionários")
            st.write("- Tarde: 6 funcionários")
            st.write("- Noite: 3 funcionários")
        
        with col2:
            st.write("**Fins de Semana:**")
            st.write("- Manhã: 3 funcionários")
            st.write("- Tarde: 3 funcionários")
            st.write("- Noite: 3 funcionários")
        
        st.write("**Restrições:**")
        st.write("- Máximo 5 dias de trabalho por semana (janela deslizante)")
        st.write("- 23 funcionários totais (2 em férias por dia)")
        st.write("- Turno único por funcionário por dia")

if __name__ == "__main__":
    main() 