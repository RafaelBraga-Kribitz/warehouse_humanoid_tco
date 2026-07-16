# Data Sources

`config/dataset_manifest.yaml` is the executable input manifest; the raw-data
register in `data/raw/MANIFEST.yaml` records access dates, licenses, and local
locations. Revisions below are pinned identifiers, not floating branches.

| Source | Repository or URL | Revision / snapshot | Use |
|---|---|---|---|
| G1 WBT pickup pillow | `unitreerobotics/G1_WBT_Inspire_Pickup_Pillow_MainCamOnly` | `24e3e4d88a5020bdb4b3046ec09b09dc56f8d1f1` | `pick_medium`; 715 episodes |
| G1 WBT clothes washer | `unitreerobotics/G1_WBT_Inspire_Put_Clothes_into_Washing_Machine_MainCamOnly` | `c0a5fb0992a0f2a2b9df3493d27c2d670a4b1c36` | `place_general`; 465 episodes |
| G1 WBT dishwasher | `unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher` | `16c01dbfcb2159783ea575acd42d1cec9b69e311` | `place_general`; 1,460 episodes |
| DiverseManip single arm | `unitreerobotics/G1_Dex1_DiverseManip_SingleArm_256x256` | `adfe712e2ac801ca7ba18c0da79e39483975cc1f` | `manipulate_diverse` |
| DiverseManip dual arm | `unitreerobotics/G1_Dex1_DiverseManip_DualArm_256x256` | `50ea572ea5f225e30e7c9116ab814a2efd73060a` | `manipulate_diverse` |
| Statistik Austria wage tables | https://www.statistik.at/statistiken/arbeitsmarkt/loehne-und-gehaelter | 2026-05-30 snapshot | Wage inputs |
| WKO collective agreement | https://www.wko.at/service/kollektivvertrag/ | 2026-05-30 snapshot | Austrian warehouse wage inputs |

Raw datasets are not duplicated by this document; use
`data/raw/MANIFEST.yaml` for source-specific licenses and access notes.
