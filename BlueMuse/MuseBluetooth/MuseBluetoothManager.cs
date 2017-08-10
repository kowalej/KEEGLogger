using BlueMuse.DataObjects;
using BlueMuse.Helpers;
using LSL;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Windows.ApplicationModel;
using Windows.Devices.Bluetooth;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Devices.Enumeration;

namespace BlueMuse.MuseBluetooth
{
    public class MuseBluetoothManager
    {
        public ObservableCollection<Muse> Muses = new ObservableCollection<Muse>();
        private DeviceWatcher museDeviceWatcher;
        private bool museDeviceWatcherReset = false;

        public MuseBluetoothManager() {}

        public void FindMuses()
        {
            string[] requestedProperties = { "System.Devices.Aep.DeviceAddress", "System.Devices.Aep.IsConnected" };
            museDeviceWatcher = DeviceInformation.CreateWatcher(Constants.ALL_AQS, requestedProperties, DeviceInformationKind.AssociationEndpoint);

            // Register event handlers before starting the watcher.
            // Added, Updated and Removed are required to get all nearby devices
            museDeviceWatcher.Added += DeviceWatcher_Added;
            museDeviceWatcher.Updated += DeviceWatcher_Updated;
            museDeviceWatcher.Removed += DeviceWatcher_Removed;

            // EnumerationCompleted and Stopped are optional to implement.
            //museDeviceWatcher.EnumerationCompleted += DeviceWatcher_EnumerationCompleted;
            museDeviceWatcher.Stopped += DeviceWatcher_Stopped;

            // Start the watcher.
            museDeviceWatcher.Start();
        }

        public void ForceRefresh()
        {
            if (museDeviceWatcher.Status != DeviceWatcherStatus.Stopped && museDeviceWatcher.Status != DeviceWatcherStatus.Stopping)
            {
                museDeviceWatcher.Stop();
                museDeviceWatcherReset = true;
                Muses.Clear();
            }
        }

        public void StartStreaming(object museId)
        {
            StartStreaming((string)museId);
        }

        public void StopStreaming(object museId)
        {
            StopStreaming((string)museId);
        }

        private async void ToggleStream(BluetoothLEDevice device, bool start)
        {
            using (var service = (await device.GetGattServicesForUuidAsync(Constants.MUSE_TOGGLE_STREAM_UUID)).Services.First())
            {
                var characteristic = (await service.GetCharacteristicsAsync()).Characteristics.First();
                //characteristic.WriteValueAsync()
            }
        }

        private async void StartStreaming(string museId)
        {
            var muse = Muses.FirstOrDefault(x => x.Id == museId);
            muse.IsStreaming = true;

            using (var device = await BluetoothLEDevice.FromIdAsync(museId))
            {
                ToggleStream(device, true);

                using (var service = (await device.GetGattServicesForUuidAsync(Constants.MUSE_DATA_SERVICE_UUID)).Services.First())
                {
                    var characteristics = (await service.GetCharacteristicsAsync()).Characteristics;
                    var channels = new List<GattCharacteristic>();
                    channels.Add(characteristics.Single(x => x.Uuid == Constants.MUSE_DATA_CHANNEL1));
                    channels.Add(characteristics.Single(x => x.Uuid == Constants.MUSE_DATA_CHANNEL2));
                    channels.Add(characteristics.Single(x => x.Uuid == Constants.MUSE_DATA_CHANNEL3));
                    channels.Add(characteristics.Single(x => x.Uuid == Constants.MUSE_DATA_CHANNEL4));
                    channels.Add(characteristics.Single(x => x.Uuid == Constants.MUSE_DATA_CHANNEL5));

                    liblsl.StreamInfo info = new liblsl.StreamInfo(muse.Name, "EEG", 5, 100, liblsl.channel_format_t.cf_float32, Package.Current.DisplayName);
                    liblsl.StreamOutlet outlet = new liblsl.StreamOutlet(info);
                    float[] data = new float[5];
                }
            }
        }

        private void StopStreaming(string museId)
        {
            var muse = Muses.FirstOrDefault(x => x.Id == museId);
            muse.IsStreaming = false;
        }

        private async void DeviceWatcher_Added(DeviceWatcher sender, DeviceInformation args)
        {
            //string address = args.Properties.Single(x => x.Key == "System.Devices.Aep.DeviceAddress").Value.ToString().Replace(":","");
            //ulong addressL = Convert.ToUInt64(address, 16);
            //BluetoothLEDevice bluetoothLeDevice = await BluetoothLEDevice.FromBluetoothAddressAsync(addressL);

            // Filter out Muses. A name filter is probably the best method currently.
            // A more robust method may be to query for a Muse specific GAAT service, however this requires devices to be powered on, even if they were previously paired with the machine.
            if (args.Name.Contains("Muse"))
            {
                using (var device = await BluetoothLEDevice.FromIdAsync(args.Id))
                {
                    Debug.WriteLine("Device Name: " + device.Name);
                    Debug.WriteLine("Current Connection Status: " + device.ConnectionStatus);
                    device.ConnectionStatusChanged += Device_ConnectionStatusChanged;
                    var services = await device.GetGattServicesAsync();
                    foreach (var service in services.Services)
                    {
                        Debug.WriteLine("Service: " + service.Uuid);
                        var characteristics = await service.GetCharacteristicsAsync();
                        foreach (var characteristic in characteristics.Characteristics)
                        {
                            Debug.WriteLine("Characteristic: " + characteristic.Uuid);
                        }
                    }

                    Muse museToUpdate = Muses.FirstOrDefault(x => x.Id == args.Id);
                    if (museToUpdate != null)
                    {
                        museToUpdate.Id = device.DeviceId;
                        museToUpdate.Name = device.Name;
                        museToUpdate.Status = device.ConnectionStatus == BluetoothConnectionStatus.Connected ? MuseConnectionStatus.Online : MuseConnectionStatus.Offline;
                    }
                    else Muses.Add(new Muse(device.Name, device.DeviceId, device.ConnectionStatus == BluetoothConnectionStatus.Connected ? MuseConnectionStatus.Online : MuseConnectionStatus.Offline));
                }
            }
        }

        private void DeviceWatcher_Removed(DeviceWatcher sender, DeviceInformationUpdate args)
        {
            // Don't remove, this causes issues.
        }

        private async void DeviceWatcher_Updated(DeviceWatcher sender, DeviceInformationUpdate args)
        {
            Muse museToUpdate = Muses.FirstOrDefault(x => x.Id == args.Id);
            using (var device = await BluetoothLEDevice.FromIdAsync(args.Id))
            {
                if (museToUpdate != null)
                {
                    museToUpdate.Id = device.DeviceId;
                    museToUpdate.Name = device.Name;
                    museToUpdate.Status = device.ConnectionStatus == BluetoothConnectionStatus.Connected ? MuseConnectionStatus.Online : MuseConnectionStatus.Offline;
                }
            }
        }

        private void Device_ConnectionStatusChanged(BluetoothLEDevice sender, object args)
        {
            Muse museToUpdate = Muses.FirstOrDefault(x => x.Id == sender.DeviceId);
            if (museToUpdate != null)
            {
                museToUpdate.Status = sender.ConnectionStatus == BluetoothConnectionStatus.Connected ? MuseConnectionStatus.Online : MuseConnectionStatus.Offline;
            }
            Debug.WriteLine(string.Format("Device: {0} is now {1}.", sender.Name, sender.ConnectionStatus));
        }

        private void DeviceWatcher_Stopped(DeviceWatcher sender, object args)
        {
            if (museDeviceWatcherReset)
            {
                museDeviceWatcherReset = false;
                museDeviceWatcher.Start();
            }
        }
    }
}
