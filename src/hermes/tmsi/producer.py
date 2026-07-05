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

import queue
import time
from typing import Optional
import numpy as np

from .sdk.device.tmsi_device import TMSiDevice
from .sdk.sample_data_server.sample_data import SampleData
from .sdk.tmsi_sdk import TMSiSDK
from .sdk.device.tmsi_device_enums import (
    DeviceInterfaceType,
    DeviceType,
    MeasurementType,
)
from .sdk.sample_data_server.sample_data_server import SampleDataServer
from .sdk.tmsi_utilities.support_functions import array_to_matrix
from .sdk.device.devices.saga.saga_API_enums import SagaBaseSampleRate
from .sdk.device.tmsi_channel import ChannelType

from hermes.base.nodes.producer import Producer
from hermes.utils.zmq_utils import PORT_BACKEND, PORT_SYNC_HOST, PORT_KILL
from hermes.utils.time_utils import get_time
from hermes.utils.types import LoggingSpec

from hermes.tmsi.data_container import TmsiDataContainer


class TmsiProducer(Producer):
    """A class to interface TMSi SAGA device."""

    def __init__(
        self,
        topic: str,
        host_ip: str,
        logging_spec: LoggingSpec,
        sensor_mapping: dict,
        base_sample_rate: Optional[str] = "Decimal",
        sampling_rate_divider: Optional[int] = 4,
        buf_len: Optional[int] = 100000,
        port_pub: Optional[str] = PORT_BACKEND,
        port_sync: Optional[str] = PORT_SYNC_HOST,
        port_killsig: Optional[str] = PORT_KILL,
        transmit_delay_sample_period_s: Optional[float] = float("nan"),
        **_,
    ) -> None:
        sampling_rate_hz = SagaBaseSampleRate[base_sample_rate].value / sampling_rate_divider

        data_out_spec = {
            "sensor_mapping": sensor_mapping,
            "sampling_rate_hz": sampling_rate_hz,
            "buf_len": buf_len,
        }

        super().__init__(
            topic=topic,
            host_ip=host_ip,
            data_out_spec=data_out_spec,
            logging_spec=logging_spec,
            sampling_rate_hz=sampling_rate_hz,
            port_pub=port_pub,
            port_sync=port_sync,
            port_killsig=port_killsig,
            transmit_delay_sample_period_s=transmit_delay_sample_period_s,
        )

        self._sensor_mapping = sensor_mapping
        self._base_sample_rate = base_sample_rate
        self._sampling_rate_divider = sampling_rate_divider

        self._sensors = sorted(sensor_mapping, key=lambda d: self._sensor_mapping[d]["channel"][0])
        self._channels = [channel for sensor in self._sensors for channel in self._sensor_mapping[sensor]["channel"]]
        self._indices = {}
        counter = 0
        for sensor, sensor_spec in self._sensor_mapping.items():
            num_channels = len(sensor_spec["channel"])
            self._indices[sensor] = [counter + i for i in range(num_channels)]
            counter += num_channels

        # Wrap data in dict, last element of data is a counter, rest are sensors in the order of `self._sensors`.
        self.build_data_dict_fn = lambda sample_block, toa_s: {
            "tmsi_data": {
                sensor: sample_block[indices].transpose((1, 0))
                for sensor, indices in self._indices.items()
            }
            | {
                "counter": sample_block[-1][:, None],
                "status": sample_block[-2][:, None],
                "toa_s": np.zeros(
                    [sample_block.shape[-1], 1], dtype=np.float64
                )
                + toa_s,
            }
        }

    @classmethod
    def create_data_container(cls, data_spec: dict) -> TmsiDataContainer:
        return TmsiDataContainer(**data_spec)

    def _ping_device(self) -> None:
        return None

    def _discover_device(self, is_wifi: bool, num_retries: int = 10) -> list[TMSiDevice]:
        TMSiSDK().discover(
            dev_type=DeviceType.saga,
            dr_interface=DeviceInterfaceType.wifi if is_wifi else DeviceInterfaceType.docked,
            ds_interface=DeviceInterfaceType.usb,
            num_retries=num_retries,
        )
        discovered_devices: list[TMSiDevice] = TMSiSDK().get_device_list(
            DeviceType.saga
        )
        return discovered_devices

    def _restart_device(self) -> None:
        # Refresh and restart the measurement on the device.
        self.device.stop_measurement()
        self.device.close()
        self.device.open()
        self.device.start_measurement(MeasurementType.SAGA_SIGNAL)

    def _connect(self) -> bool:
        is_success = False
        try:
            discovered_devices: list[TMSiDevice] = self._discover_device(is_wifi=True, num_retries=10)

            if discovered_devices:
                # Get the handle to the first discovered device and open the connection.
                for device in discovered_devices:
                    if device.get_dr_interface() == DeviceInterfaceType.wifi:
                        # Open the connection to SAGA.
                        self.device = device
                        self.device.open()
                        break
            else:
                discovered_devices: list[TMSiDevice] = self._discover_device(is_wifi=False, num_retries=10)
                # Get the handle to the first discovered device and open the connection.
                for device in discovered_devices:
                    if device.get_dr_interface() == DeviceInterfaceType.docked:
                        # Open the connection to SAGA.
                        self.device = device
                        self.device.open()
                        break

            # Enable only the channels that are specified in the sensor mapping.
            self.device.set_device_active_channels(list(range(90)), False)
            self.device.set_device_active_channels(self._channels, True)

            # Configure sampling rate of the selected channel types, specified in the sensor mapping.
            enabled_ports = set(map(lambda x: x["port"], self._sensor_mapping.values()))
            for port in enabled_ports:
                self.device.set_device_sampling_config(
                    base_sample_rate=SagaBaseSampleRate[self._base_sample_rate],
                    channel_type=ChannelType[port],
                    channel_divider=self._sampling_rate_divider,
                )

            # TODO: display which sensors detected at which port.
            # Retrieve all channels from the device and update which should be enabled
            # device_channels: list[SagaChannel] = self.device.get_device_channels()
            # for channel in device_channels:
            #     sensor_info: SagaSensor = channel.get_sensor_information()
                # if (channel.get_channel_type() == ChannelType.AUX):
                #     pass
                # print(
                #     f"Current expected connected devices: {self._sensors}\n",
                #     f"Make sure they are connected during setup and in the right port",
                #     flush=True,
                # )

            if self.device.get_dr_interface() != DeviceInterfaceType.wifi:
                # Choose the desired DR-DS interface type.
                self.device.set_device_interface(DeviceInterfaceType.wifi)

                # Close the connection to the device (with the original interface type).
                self.device.close()

                time.sleep(1)

                print("[TMSi] WiFi setup starting.", flush=True)

                discovered_devices: list[TMSiDevice] = self._discover_device(is_wifi=True, num_retries=10)

                if discovered_devices:
                    # Get the handle to the first discovered device and open the connection.
                    for device in discovered_devices:
                        if device.get_dr_interface() == DeviceInterfaceType.wifi:
                            # Open the connection to SAGA.
                            self.device = device
                            self.device.open()
                            break
                else:
                    return False

            # Check the current bandwidth that's in use.
            current_bandwidth = self.device.get_device_bandwidth()
            print(
                "[TMSi] The current bandwidth in use is {:} bit/s".format(
                    current_bandwidth["in use"]
                ),
                flush=True,
            )
            print(
                "[TMSi] Maximum bandwidth for wifi measurements is {:} bit/s".format(
                    current_bandwidth["wifi"]
                ),
                flush=True,
            )

            self.data_sampling_server = SampleDataServer()
            self.data_queue = queue.Queue()
            self.data_sampling_server.register_consumer(
                self.device.get_id(), self.data_queue
            )

            self.device.start_measurement(MeasurementType.SAGA_SIGNAL)

            print(
                "[TMSi] Successfully connected SAGA.", flush=True
            )
            is_success = True
        except Exception as e:
            print(e)
            print("[TMSi] Failed to connect to SAGA.", flush=True)

        return is_success

    def _keep_samples(self) -> None:
        # Clear the buffer queue of accumulated values during the system bring-up.
        try:
            while True:
                self.data_queue.get_nowait()
        except queue.Empty:
            return

    def _process_data(self) -> None:
        try:
            new_data: SampleData = self.data_queue.get(timeout=1.0)
            toa_s = get_time()
            sample_block = np.array(
                array_to_matrix(new_data.samples, new_data.num_samples_per_sample_set)
            )
            tag: str = "%s.data" % self.topic

            data = self.build_data_dict_fn(sample_block, toa_s)
            self._publish(tag=tag, process_time_s=get_time(), data=data)
        except queue.Empty:
            if not self._is_continue_capture:
                self._send_end_packet()
            else:
                print(
                    "[TMSi] Timed out, reconnecting to SAGA.", flush=True
                )
                self._restart_device()

    def _stop_new_data(self):
        # Stop receiving data from TMSi, to correctly wrap up the measurement.
        self.data_sampling_server.unregister_consumer(self.device.get_id(), self.data_queue)

    def _cleanup(self) -> None:
        # Set the DR-DS interface type back to docked.
        self.device.stop_measurement()
        self.device.close()
        super()._cleanup()
