using BlueMuse.Helpers;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace BlueMuse.DataObjects
{
    public enum MuseConnectionStatus
    {
        Online = 0,
        Offline = 1
    }

    public class Muse : ObservableObject
    {
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

        public Muse(string name, string Id, MuseConnectionStatus status)
        {
            this.Name = name;
            this.Id = Id;
            this.Status = status;
        }
    }
}
