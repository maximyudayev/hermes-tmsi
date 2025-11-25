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
Using the device follows the standard [configuration file specification](https://maximyudayev.github.io/hermes/) process of HERMES nodes.

> [!NOTE]
> [These modalities](https://github.com/maximyudayev/hermes-tmsi/blob/main/src/hermes/tmsi/stream.py#L44-L87) are collected out-of-the-box. Change them and the [SDK configuration](https://github.com/maximyudayev/hermes-tmsi/blob/main/src/hermes/tmsi/producer.py#L132-L159) to add or replace modalities with sensors of choice.

## Citation
When using any parts of this repository outside of its intended use, please cite the parent project [HERMES](https://github.com/maximyudayev/hermes).
