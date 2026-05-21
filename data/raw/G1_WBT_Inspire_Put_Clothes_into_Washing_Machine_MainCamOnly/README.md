---
license: apache-2.0
task_categories:
- robotics
tags:
- LeRobot
configs:
- config_name: default
  data_files: G1_WB_Dex5_Put_Clothes_into_Washing_Machine/data/*/*.parquet
---

# Data Structure

## Observations

### `observation.state.ee_state` (12)
End-effector states of the robot.
- Computed via forward kinematics (FK) from the root link to the left and right end-effectors.
- Includes the contribution of the waist.
- Represented as concatenated poses of both end-effectors.

---

### `observation.state.hand_state` (12 or 2)
Finger states for both hands. The dimensionality depends on the hand type.

#### Inspire Hand (range: 0.0 – 1.0, open → close)
Per hand:
1. Index finger  
2. Middle finger  
3. Ring finger  
4. Little finger  
5. Thumb (open/close)  
6. Thumb (lateral tilt)

---

#### BrainCo Hand (range: 0.0 – 1.0, open → close)
Per hand:
1. Thumb (open/close)  
2. Thumb (lateral tilt)  
3. Index finger  
4. Middle finger  
5. Ring finger  
6. Little finger  

---

#### Dex1 Hand (range: 5.5 – 0.0, open → close)
Per hand:
1. Open/close  

---

### `observation.state.robot_q_current` (36)
Current robot configuration.
- First 7 values:
  - Root position: (x, y, z)
  - Root orientation: quaternion (w, x, y, z)
- Remaining 29 values:
  - Robot joint positions.

---

## Actions

### `action.ee_action` (12)
Target end-effector states.
- Defined using forward kinematics (FK) from the root link to both end-effectors.
- Includes waist motion.

---

### `action.hand_cmd` (12 or 2)
Commanded finger actions. The dimensionality depends on the hand type.

#### Inspire Hand (range: 0.0 – 1.0, open → close)
Per hand:
1. Index finger  
2. Middle finger  
3. Ring finger  
4. Little finger  
5. Thumb (open/close)  
6. Thumb (lateral tilt)

---

#### BrainCo Hand (range: 0.0 – 1.0, open → close)
Per hand:
1. Thumb (open/close)  
2. Thumb (lateral tilt)  
3. Index finger  
4. Middle finger  
5. Ring finger  
6. Little finger  

---

#### Dex1 Hand (range: 5.5 – 0.0, open → close)
Per hand:
1. Open/close  

---

### `action.robot_q_desired` (36)
Desired robot configuration.
- First 7 values:
  - Target root position: (x, y, z)
  - Target root orientation: quaternion (w, x, y, z)
- Remaining 29 values:
  - Target joint positions.

---


# Acknowledgements

This dataset was created using the [LeRobot](https://github.com/huggingface/lerobot) framework.