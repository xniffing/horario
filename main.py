from ortools.sat.python import cp_model

# --- 1. Define Model and Data ---
model = cp_model.CpModel()

# --- Sets ---
# Assuming a planning horizon, e.g., 2 weeks (14 days)
num_days = 14
days = range(num_days)
workers = range(23) # Total workers
shifts = ['manha', 'central', 'tarde', 'noite']
weekday_shifts = ['manha', 'central', 'tarde', 'noite']
weekend_shifts = ['manha', 'tarde', 'noite'] # No 'central' shift on weekends

# Define specific shifts per day
# Example: day 0 is Monday, day 5 is Saturday, day 6 is Sunday
shifts_by_day_type = {}
for d in days:
    if d % 7 == 5 or d % 7 == 6: # Saturday or Sunday
        shifts_by_day_type[d] = weekend_shifts
    else: # Monday to Friday
        shifts_by_day_type[d] = weekday_shifts

# Required staff per shift and day type
required_staff_weekday = {
    'manha': 6,
    'central': 2,
    'tarde': 6,
    'noite': 3
}
required_staff_weekend = {
    'manha': 3,
    'tarde': 3,
    'noite': 3
}

# You might pre-define which 2 people are on vacation each day
# For simplicity in this outline, let's assume availability is handled by the solver
# and we ensure only 21 people are active daily.
# A more robust solution might have a pre-defined 'vacation_schedule' array.
# e.g., vacation_schedule[worker_id][day_id] = True/False

# --- 2. Decision Variables ---
# x_w_d_s: Binary variable, 1 if worker 'w' is assigned to day 'd' and shift 's'
x = {}
for w in workers:
    for d in days:
        for s in shifts_by_day_type[d]: # Only create variables for valid shifts
            x[(w, d, s)] = model.new_bool_var(f'x_{w}_{d}_{s}')

# --- 3. Constraints ---

# Constraint 1: Unique People Per Shift (and per day overall)
# Each worker can work at most one shift per day.
for w in workers:
    for d in days:
        model.add_at_most_one([x[(w, d, s)] for s in shifts_by_day_type[d]])

# Constraint 2: Required Staff Per Shift
for d in days:
    for s in shifts_by_day_type[d]:
        if d % 7 == 5 or d % 7 == 6: # Weekend
            model.add(sum(x[(w, d, s)] for w in workers) == required_staff_weekend[s])
        else: # Weekday
            model.add(sum(x[(w, d, s)] for w in workers) == required_staff_weekday[s])

# Constraint 3: Total Workers Available (21 per day, 2 on vacation)
# This can be implicitly handled by the sum of required staff per day,
# but an explicit constraint ensures total assigned don't exceed capacity.
# Sum of required staff per weekday: 6+2+6+3 = 17
# Sum of required staff per weekend: 3+3+3 = 9
# Since these sums (17, 9) are always <= 21, the vacation constraint
# is implicitly satisfied *if a solution exists*.
# If you need to *explicitly* model which 2 people are on vacation, you'd do:
# 3a. Define vacation status for each worker and day
#    is_on_vacation[w][d] = model.new_bool_var(f'vac_{w}_{d}')
# 3b. Constraint: Exactly 2 workers are on vacation each day
#    for d in days:
#        model.add(sum(is_on_vacation[w][d] for w in workers) == 2)
# 3c. Constraint: If worker is on vacation, they cannot work a shift
#    for w in workers:
#        for d in days:
#            for s in shifts_by_day_type[d]:
#                model.add_implication(is_on_vacation[w][d], x[(w, d, s)].not_())
#
# Alternatively, if vacation is pre-assigned (simpler):
# predefined_vacations = {(worker_id, day_id), (worker_id, day_id), ...}
# for (w_vac, d_vac) in predefined_vacations:
#    for s_vac in shifts_by_day_type[d_vac]:
#        model.add(x[(w_vac, d_vac, s_vac)] == 0)


# Constraint 4: No more than 5 days work per week (rolling window)
# For each worker, sum their active days over a 7-day rolling window.
for w in workers:
    for start_day in range(num_days - 6): # Iterate through all possible 7-day windows
        # Count how many days in the 7-day window the worker is assigned to any shift
        working_days_in_window = []
        for d in range(start_day, start_day + 7):
            # Create a boolean expression: worker w works on day d if assigned to any shift
            works_on_day = model.new_bool_var(f'works_{w}_{d}')
            # If any shift is assigned, works_on_day must be true
            model.add_bool_or([x[(w, d, s)] for s in shifts_by_day_type[d]]).only_enforce_if(works_on_day)
            # If no shift is assigned, works_on_day must be false
            model.add(sum(x[(w, d, s)] for s in shifts_by_day_type[d]) == 0).only_enforce_if(works_on_day.Not())
            working_days_in_window.append(works_on_day)
        
        # Constraint: no more than 5 working days in any 7-day window
        model.add(sum(working_days_in_window) <= 5)

# --- 4. Objective Function (Optional but Recommended) ---
# For instance, minimize the number of consecutive shifts of the same type,
# or balance workload, or maximize preferred shifts.
# For a basic feasible schedule, you might not need an objective,
# but it helps the solver find "good" solutions.
# Example: Minimize total weekend shifts for employees (to balance work-life)
# model.minimize(sum(x[(w,d,s)] for w in workers for d in days if d % 7 == 5 or d % 7 == 6 for s in shifts_by_day_type[d]))

# --- 5. Solve the Model ---
solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True # Useful for debugging
status = solver.solve(model)

# --- 6. Print the Solution ---
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f'Solution status: {solver.status_name(status)}')
    print(f'Optimal objective value: {solver.objective_value}')

    schedule = {}
    for d in days:
        print(f"\n--- Day {d} ({'Weekend' if d % 7 == 5 or d % 7 == 6 else 'Weekday'}) ---")
        schedule[d] = {}
        for s in shifts_by_day_type[d]:
            assigned_workers = []
            for w in workers:
                if solver.value(x[(w, d, s)]) == 1:
                    assigned_workers.append(w)
            print(f"  Shift {s}: {assigned_workers}")
            schedule[d][s] = assigned_workers

    # Verify 5-day week constraint for some workers (optional, for debugging)
    for w in workers:
        working_days_count = 0
        for d in days:
            # Check if worker w works on day d by looking at any shift assignment
            works_on_day = any(solver.value(x[(w, d, s)]) == 1 for s in shifts_by_day_type[d])
            if works_on_day:
                working_days_count += 1
        print(f"Worker {w} worked {working_days_count} days in total period.")


else:
    print(f"No solution found. Status: {solver.status_name(status)}")

print("\nSolver statistics:")
print(f"  - conflicts: {solver.num_conflicts}")
print(f"  - branches : {solver.num_branches}")
print(f"  - wall time: {solver.wall_time}s")