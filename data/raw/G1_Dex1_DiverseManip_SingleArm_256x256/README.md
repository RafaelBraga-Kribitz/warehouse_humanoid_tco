---
license: apache-2.0
task_categories:
- robotics
tags:
- LeRobot
configs:
- config_name: default
  data_files: data/*/*.parquet
---

This dataset was created using [LeRobot](https://github.com/huggingface/lerobot).

## Dataset Description

- **Homepage:** [unitreerobotics](https://github.com/unitreerobotics)
- **License:** apache-2.0

- **Task Objective:** Organize and tidy the items on the table.  
- **Operation Duration:** Each operation takes approximately 20 to 40 seconds.  
- **Recording Frequency:** 30 Hz.  
- **Robot Type:** 7-DOF single-arm G1 robot.  
- **End Effector:** Gripper.  
- **Dual-Arm Operation:** No.  
- **Image Resolution:** 256x256.  
- **Camera Positions:** head-mounted (binocular cameras).  
- **Data Content:**  
• Robot's current state.  
• Robot's next action.  
• Current camera view images.  
- **Robot Initial Posture:** The first robot state in each dataset entry.  
- **Object Placement:** Randomly placed within the robot arm's motion range and the field of view of the robot's head-mounted camera.  
- **Camera View:** Follow the guidelines in **Part 5** of [AVP Teleoperation Documentation](https://github.com/unitreerobotics/avp_teleoperate).  


<table>
  <tr>
    <td><img src="assets/0.gif" width="200px" /></td>
    <td><img src="assets/1.gif" width="200px" /></td>
    <td><img src="assets/2.gif" width="200px" /></td>
    <td><img src="assets/3.gif" width="200px" /></td>
  </tr>
</table>


- **Important Notes:**  
1. This is a G1 diversity dataset that can be used for video generation models, world models, and other applications \[[Lee et al., 2018](#citation)\].  
2. If you want to use the lerobotv2.1 format, refer to this file for conversion: [convert_v3_to_v2.py](https://github.com/NVIDIA/Isaac-GR00T/blob/main/scripts/lerobot_conversion/convert_v3_to_v2.py)
3. Due to the inability to precisely describe spatial positions, adjust the scene to closely match the first frame of the dataset after installing the hardware as specified in **Part 5** of [AVP Teleoperation Documentation](https://github.com/unitreerobotics/avp_teleoperate).  
4. Data collection is not completed in a single session, and variations between data entries exist. Ensure these variations are accounted for during model training.  


## Dataset Structure

[meta/info.json](meta/info.json):
```json
{
    "codebase_version": "v3.0",
    "robot_type": "Unitree_G1_Dex1",
    "total_episodes": 468,
    "total_frames": 331555,
    "total_tasks": 1,
    "chunks_size": 1000,
    "data_files_size_in_mb": 100,
    "video_files_size_in_mb": 500,
    "fps": 30,
    "splits": {
        "train": "0:468"
    },
    "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
    "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
    "features": {
        "observation.state": {
            "dtype": "float32",
            "shape": [
                16
            ],
            "names": [
                [
                    "kLeftShoulderPitch",
                    "kLeftShoulderRoll",
                    "kLeftShoulderYaw",
                    "kLeftElbow",
                    "kLeftWristRoll",
                    "kLeftWristPitch",
                    "kLeftWristYaw",
                    "kRightShoulderPitch",
                    "kRightShoulderRoll",
                    "kRightShoulderYaw",
                    "kRightElbow",
                    "kRightWristRoll",
                    "kRightWristPitch",
                    "kRightWristYaw",
                    "kLeftGripper",
                    "kRightGripper"
                ]
            ]
        },
        "action": {
            "dtype": "float32",
            "shape": [
                16
            ],
            "names": [
                [
                    "kLeftShoulderPitch",
                    "kLeftShoulderRoll",
                    "kLeftShoulderYaw",
                    "kLeftElbow",
                    "kLeftWristRoll",
                    "kLeftWristPitch",
                    "kLeftWristYaw",
                    "kRightShoulderPitch",
                    "kRightShoulderRoll",
                    "kRightShoulderYaw",
                    "kRightElbow",
                    "kRightWristRoll",
                    "kRightWristPitch",
                    "kRightWristYaw",
                    "kLeftGripper",
                    "kRightGripper"
                ]
            ]
        },
        "observation.images.cam_left_high": {
            "dtype": "video",
            "shape": [
                256,
                256,
                3
            ],
            "names": [
                "height",
                "width",
                "channel"
            ],
            "info": {
                "video.height": 256,
                "video.width": 256,
                "video.codec": "av1",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "video.fps": 30,
                "video.channels": 3,
                "has_audio": false
            }
        },
        "observation.images.cam_right_high": {
            "dtype": "video",
            "shape": [
                256,
                256,
                3
            ],
            "names": [
                "height",
                "width",
                "channel"
            ],
            "info": {
                "video.height": 256,
                "video.width": 256,
                "video.codec": "av1",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "video.fps": 30,
                "video.channels": 3,
                "has_audio": false
            }
        },
        "timestamp": {
            "dtype": "float32",
            "shape": [
                1
            ],
            "names": null
        },
        "frame_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "episode_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "task_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        }
    }
}
```


## Citation

**BibTeX:**

```bibtex
@article{lee2018stochastic,
  title={Stochastic Adversarial Video Prediction},
  author={Lee, Alex X. and Zhang, Richard and Ebert, Frederik and Abbeel, Pieter and Finn, Chelsea and Levine, Sergey},
  journal={arXiv preprint arXiv:1804.01523},
  year={2018},
  url={https://arxiv.org/abs/1804.01523}
}
```