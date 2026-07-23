# Ex 1 - Manufacturing Quality Control (NumPy)
# URK24CS1021
import numpy as np

np.random.seed(1021)  # keep the run reproducible

# 1. hourly defect rates (%) for 24-hour production, random 0.1 - 5.0
defects = np.round(np.random.uniform(0.1, 5.0, 24), 2)
print("Hourly defect rates (%):")
print(defects)

# 2. defect rate at hour 12 (indexing)
print("\nDefect rate at hour 12:", defects[12], "%")

# 3. night shift 20:00 - 06:00 (slicing across midnight)
night = np.concatenate((defects[20:], defects[:7]))
print("\nNight shift (20:00 to 06:00):")
print(night)

# 4. reshape into (3, 8) for shift analysis
shifts = defects.reshape(3, 8)
print("\nReshaped into 3 shifts x 8 hours:")
print(shifts)

# 5. iterate to find problem hours (> 3%)
print("\nProblem hours (defect rate > 3%):")
for hour, rate in enumerate(defects):
    if rate > 3:
        print("  Hour", hour, "->", rate, "%")

# 6. join with a temperature array (random 24 values)
temp = np.round(np.random.uniform(18, 30, 24), 1)
combined = np.vstack((defects, temp))
print("\nDefects joined with temperature (2 x 24):")
print(combined)

# 7. split into 3 shifts
shift1, shift2, shift3 = np.split(defects, 3)
print("\nSplit into three shifts:")
print("Shift 1:", shift1)
print("Shift 2:", shift2)
print("Shift 3:", shift3)

# 8. critical defects (> 4%)
print("\nCritical defects (> 4%):", defects[defects > 4])

# 9. sort defects in ascending order
print("\nSorted (ascending):")
print(np.sort(defects))

# 10. filter acceptable range (0.5 - 1.5%)
acceptable = defects[(defects >= 0.5) & (defects <= 1.5)]
print("\nAcceptable range (0.5 - 1.5%):", acceptable)
