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
        public static readonly Guid MUSE_DATA_SERVICE_UUID = new Guid("0000fe8d-0000-1000-8000-00805f9b34fb");
    }
}
