using System;

using Windows.Devices.Enumeration;
using System.Diagnostics;
using Windows.Devices.Bluetooth;
using BlueMuse.Helpers;
using BlueMuse.DataObjects;
using System.Text.RegularExpressions;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Input;

// The Blank Page item template is documented at https://go.microsoft.com/fwlink/?LinkId=402352&clcid=0x409

namespace BlueMuse.ViewModels
{
    /// <summary>
    /// An empty page that can be used on its own or navigated to within a Frame.
    /// </summary>
    public class MainPageVM : ObservableObject
    {
        public ObservableCollection<Muse> Muses = new ObservableCollection<Muse>();
        private DeviceWatcher museDeviceWatcher;
        private bool museDeviceWatcherReset = false;
            
        public MainPageVM()
        {
            FindMuses();
        }

        private void FindMuses()
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

        private void DeviceWatcher_Stopped(DeviceWatcher sender, object args)
        {
            if (museDeviceWatcherReset)
            {
                museDeviceWatcherReset = false;
                museDeviceWatcher.Start();
            }
        }

        private void ResetMuseDeviceWatcher()
        {
            if (museDeviceWatcher.Status != DeviceWatcherStatus.Stopped && museDeviceWatcher.Status != DeviceWatcherStatus.Stopping)
            {
                museDeviceWatcher.Stop();
                museDeviceWatcherReset = true;
                Muses.Clear();
            }
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

        private ICommand forceRefresh;
        public ICommand ForceRefresh
        {
            get
            {
                return forceRefresh ?? (forceRefresh = new CommandHandler(() =>
                {
                    ResetMuseDeviceWatcher();
                }, true));
            }
        }

        async void StreamMuse(Muse muse)
        {
            var devices = await DeviceInformation.FindAllAsync("System.Devices.DevObjectType:=5 AND System.Devices.Aep.ProtocolId:=\"{BB7BB05E-5972-42B5-94FC-76EAA7084D49}\"");
            //if (devices.Count == 0)
            //    return;
            //Connect to the service
            //var service = await GattDeviceService.FromIdAsync(devices[0].Id);
            //if (service == null)
            //    return;
            //Obtain the characteristic we want to interact with
            //var characteristic = await service.GetCharacteristicsForUuidAsync(BluetoothUuidHelper.FromShortId(0x2A00));
            //Read the value
            //var deviceNameBytes = (await characteristic.Characteristics[0].ReadValueAsync()).Value.ToArray();
            //Convert to string
            //var deviceName = Encoding.UTF8.GetString(deviceNameBytes, 0, deviceNameBytes.Length);
        }
    }
}
