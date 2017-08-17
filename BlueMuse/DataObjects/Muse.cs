using BlueMuse.Helpers;
using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using Windows.Devices.Bluetooth;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Foundation;

namespace BlueMuse.DataObjects
{
    public enum MuseConnectionStatus
    {
        Online = 0,
        Offline = 1
    }

    public class MuseSample
    {
        public DateTime[] timeStamps;
        public DateTime BaseTimeStamp
        {
            get
            {
                return timeStamps[11];
            }
            set
            {
                for(int i = 0; i < 12; i++)
                {
                    timeStamps[i] = value.AddMilliseconds(-((12 - i) * 4)); // Adjust time considering each samples is 4ms.
                }
                timeStamps[11] = value;
            }
        }
        public DateTime[] TimeStamps { get { return timeStamps; } }

        public SortedDictionary<Guid, float[]> ChannelData;

        public MuseSample()
        {
            ChannelData = new SortedDictionary<Guid, float[]>();
            timeStamps = new DateTime[12];
        }
    }

    public class Muse : ObservableObject
    {
        public BluetoothLEDevice Device { get; set; }
        public GattDeviceService DeviceService { get; set; }
        public Dictionary<UInt16, MuseSample> SampleBuffer { get; set; }
        public TypedEventHandler<GattCharacteristic, GattValueChangedEventArgs>[] channelEventHandlers;
        public TypedEventHandler<GattCharacteristic, GattValueChangedEventArgs>[] ChannelEventHandlers
        {
            get
            {
                if (channelEventHandlers == null)
                    channelEventHandlers = new TypedEventHandler<GattCharacteristic, GattValueChangedEventArgs>[5];
                return channelEventHandlers;
            }
            set { channelEventHandlers = value; }
        }

        private string name;
        public string Name { get { return name; } set { SetProperty(ref name, value); OnPropertyChanged(nameof(LongName)); } }

        private string id;
        public string Id { get { return id; } set { SetProperty(ref id, value); OnPropertyChanged(nameof(MacAddress)); OnPropertyChanged(nameof(LongName)); } }

        private MuseConnectionStatus status;
        public MuseConnectionStatus Status
        {
            get { return status; }
            set
            {
                SetProperty(ref status, value);
                OnPropertyChanged(nameof(CanStream));
                if (value == MuseConnectionStatus.Offline && isStreaming == true)
                {
                    IsStreaming = false;
                }
            }
        }

        private bool isStreaming;
        public bool IsStreaming { get { return isStreaming; } set { SetProperty(ref isStreaming, value); } }

        private bool isSelected;
        public bool IsSelected { get { return isSelected; } set { SetProperty(ref isSelected, value); } }

        private int streamingPort;
        public int StreamingPort { get { return streamingPort; } set { SetProperty(ref streamingPort, value); } }

        public bool CanStream { get { return status == MuseConnectionStatus.Online; } }

        public string LongName { get { return string.Format("{0} ({1})", Name, MacAddress); } }

        public string MacAddress
        {
            get
            {
                Regex deviceIdRegex = new Regex(@"^*(\w{2}:){5}\w{2}");
                string museId = Id;
                Match matches = deviceIdRegex.Match(museId);
                if (matches.Success)
                    museId = matches.Value;
                return museId;
            }
        }

        public Muse(BluetoothLEDevice device, string name, string id, MuseConnectionStatus status)
        {
            Device = device;
            Name = name;
            Id = id;
            Status = status;
        }
    }
}
