############
#
# Copyright (c) 2024-2026 Maxim Yudayev and KU Leuven eMedia Lab
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Created 2024-2025 for the KU Leuven AidWear, AidFOG, and RevalExo projects
# by Maxim Yudayev [https://yudayev.com].
#
# ############

from typing import Optional, OrderedDict

from hermes.base.data_container import DataContainer


class TmsiDataContainer(DataContainer):
    """A structure to store TMSi SAGA stream's data."""

    def __init__(
        self,
        sensor_mapping: dict,
        batch_send_rate_hz: Optional[int] = 20,
        sampling_rate_hz: Optional[int] = 1000,
        buf_len: Optional[int] = 100000,
        transmission_delay_period_s: Optional[int] = None,
        **_,
    ) -> None:
        super().__init__()

        self._sensor_mapping = sensor_mapping
        self._sampling_rate_hz = sampling_rate_hz
        self._batch_send_rate_hz = batch_send_rate_hz
        self._transmission_delay_period_s = transmission_delay_period_s

        self._define_data_notes()

        for sensor_name, sensor_spec in sensor_mapping.items():
            self.add_channel(
                bundle_name="tmsi_data",
                channel_name=sensor_name,
                data_type=sensor_spec["dtype"],
                sample_size=sensor_spec["shape"],
                buf_len=buf_len,
                sampling_rate_hz=self._sampling_rate_hz,
                data_notes=self._data_notes["tmsi_data"].get(sensor_name, {}),
            )

        self.add_channel(
            bundle_name="tmsi_data",
            channel_name="counter",
            data_type="uint32",
            sample_size=[1],
            buf_len=buf_len,
            sampling_rate_hz=self._sampling_rate_hz,
            data_notes=self._data_notes["tmsi_data"]["counter"],
        )
        self.add_channel(
            bundle_name="tmsi_data",
            channel_name="toa_s",
            data_type="float64",
            sample_size=[1],
            buf_len=buf_len,
            sampling_rate_hz=self._sampling_rate_hz,
            is_measure_rate_hz=True,
            data_notes=self._data_notes["tmsi_data"]["toa_s"],
        )

        if self._transmission_delay_period_s:
            self.add_channel(
                bundle_name="tmsi_connection",
                channel_name="transmission_delay",
                data_type="float32",
                sample_size=[1],
                buf_len=buf_len,
                sampling_rate_hz=1.0 / self._transmission_delay_period_s,
            )

    def get_fps(self) -> dict[str, float | None]:
        return {"tmsi_data": super()._get_fps("tmsi_data", "toa_s")}

    def _define_data_notes(self):
        self._data_notes = {}
        self._data_notes["tmsi_data"] = {}
        self._data_notes["tmsi_data"]["ecg"] = OrderedDict(
            [
                (
                    "Notes",
                    f"Electrocardiogram. Sampled at {self._sampling_rate_hz} Hz, received in bursts at {self._batch_send_rate_hz} Hz.",
                ),
                (
                    "TMSi channel",
                    str(self._sensor_mapping.get("ecg", {"channel": [65, 66]})["channel"]),
                ),
            ]
        )
        self._data_notes["tmsi_data"]["breath"] = OrderedDict(
            [
                (
                    "Notes",
                    f"Respiration rate measured by the abdominal circumference variation. Sampled at {self._sampling_rate_hz} Hz, received in bursts at {self._batch_send_rate_hz} Hz.",
                ),
                (
                    "TMSi channel",
                    str(self._sensor_mapping.get("breath", {"channel": [69]})["channel"]),
                ),
            ]
        )
        self._data_notes["tmsi_data"]["gsr"] = OrderedDict(
            [
                (
                    "Notes",
                    f"Galvanic skin response. Sampled at {self._sampling_rate_hz} Hz, received in bursts at {self._batch_send_rate_hz} Hz.",
                ),
                (
                    "TMSi channel",
                    str(self._sensor_mapping.get("gsr", {"channel": [72]})["channel"]),
                ),
            ]
        )
        self._data_notes["tmsi_data"]["spo2"] = OrderedDict(
            [
                (
                    "Notes",
                    f"Peripheral capillary oxygen saturation. Sampled at {self._sampling_rate_hz} Hz, received in bursts at {self._batch_send_rate_hz} Hz.",
                ),
                (
                    "TMSi channel",
                    str(self._sensor_mapping.get("spo2", {"channel": [78]})["channel"]),
                ),
            ]
        )
        self._data_notes["tmsi_data"]["counter"] = OrderedDict(
            [
                (
                    "Notes",
                    f"Monotonically increasing index of the sensor samples arriving in chunks. Maps one-to-one for every individual sensor measurement.",
                ),
            ]
        )
        self._data_notes["tmsi_data"]["toa_s"] = OrderedDict(
            [
                (
                    "Notes",
                    f"Time of arrival of the samples w.r.t. system clock. Repeated for samples arrived in the same burst. Changes at {self._batch_send_rate_hz} Hz",
                ),
            ]
        )
