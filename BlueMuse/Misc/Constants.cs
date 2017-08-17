using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlueMuse
{
    static class Constants
    {
        public static readonly string ALL_AQS = "System.Devices.DevObjectType:=5 AND System.Devices.Aep.ProtocolId:=\"{BB7BB05E-5972-42B5-94FC-76EAA7084D49}\""; // Wildcard based "Muse*" filter - not supported it seems. AND (System.ItemNameDisplay:~\"Muse*\" OR System.Devices.Aep.Bluetooth.IssueInquiry:=System.StructuredQueryType.Boolean#True)";

        // Starts and stops streaming.
        public static readonly Guid MUSE_TOGGLE_STREAM_UUID = new Guid("273e0001-4c4d-454d-96be-f03bac821358");
        public static readonly byte[] MUSE_TOGGLE_STREAM_START = new byte[3] {0x02, 0x64, 0x0a};
        public static readonly byte[] MUSE_TOGGLE_STREAM_STOP = new byte[3] { 0x02, 0x68, 0x0a };

        // These are the data channels.
        public static readonly Guid MUSE_DATA_SERVICE_UUID = new Guid("0000fe8d-0000-1000-8000-00805f9b34fb");
        public static readonly Guid MUSE_DATA_CHANNEL1 = new Guid("273e0003-4c4d-454d-96be-f03bac821358");
        public static readonly Guid MUSE_DATA_CHANNEL2 = new Guid("273e0004-4c4d-454d-96be-f03bac821358");
        public static readonly Guid MUSE_DATA_CHANNEL3 = new Guid("273e0005-4c4d-454d-96be-f03bac821358");
        public static readonly Guid MUSE_DATA_CHANNEL4 = new Guid("273e0006-4c4d-454d-96be-f03bac821358");
        public static readonly Guid MUSE_DATA_CHANNEL5 = new Guid("273e0007-4c4d-454d-96be-f03bac821358");
    }
}
