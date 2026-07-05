# HERMES - TMSi SAGA

Support package to interface the [TMSi SAGA](https://www.tmsi.artinis.com/saga) commercial multimodal physiological signal acquisition device in [HERMES](https://github.com/maximyudayev/hermes), using OEM's open-source [Python SDK](https://artinis-medical-systems-b-v.github.io/TMSi-Documentation-Python-Interface/).

> [!NOTE]
> The 2023-2024 version of the OEM Python SDK is released under the Apache-2.0 license and is packaged as a dependency of this module under `hermes.tmsi.sdk` without changes to the source. A new version has [since been released](https://artinis-medical-systems-b-v.github.io/TMSi-Documentation-Python-Interface/), but not yet integrated nor tested.

> [!IMPORTANT]
> TMSi SAGA Python SDK is Windows-only and requires `Python>=3.9`.

## Installation
Node available under the same HERMES namespace of `hermes.tmsi` as `TmsiProducer`.

Follow [these instructions](https://artinis-medical-systems-b-v.github.io/TMSi-Documentation-Python-Interface/getting_started/installation.html) to prepare the desktop with necessary drivers.

### From PyPI
```bash
pip install pysio-hermes-tmsi
```

### From source
```bash
git clone https://github.com/maximyudayev/hermes-tmsi.git
pip install -e hermes-tmsi
```

## Usage
Using the device follows the standard [configuration file specification](https://yudayev.com/hermes) process of HERMES nodes.

> [!IMPORTANT]
> Channels specified in YAML must match the actual port to which an analog sensor is connected. Else wrong sensors will be read out.
> | Device | Port | Channel |
> | - | - | - |
> | | UNI | [1-32] OR [1-64][^1] |
> | ECG (1-ch) | BIP-01 | [65] |
> | Respiration (1-ch) | AUX-01 | [69] |
> | GSR (1-ch) | AUX-02 | [72] |
> | SpO2 | DIGI | [79] |

[^1]: 32-/64-channel unipolar connections available, depending on the SAGA device.

> [!IMPORTANT]
> 1. Always add the patient ground lead to ensure physiological signals on BIP and AUX ports are not floating.
> 1. Add stress relief loops on the sensor leads to avoid motion artifacts in the data, when accidentally tagging on the wires.

## Citation
When using any parts of this repository outside of its intended use, please cite the parent project [HERMES](https://github.com/maximyudayev/hermes).
