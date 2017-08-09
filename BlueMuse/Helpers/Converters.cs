using System;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Data;

namespace BlueMuse.Helpers
{
    public static class BooleanExtensions
    {
        public static string ToYesNoString(this bool value)
        {
            return value ? "Yes" : "No";
        }
    }

    public class GenericStringFormatter : Windows.UI.Xaml.Data.IValueConverter
    {
        // This converts the value object to the string to display.
        // This will work with most simple types.
        public object Convert(object value, Type targetType,
            object parameter, string language)
        {
            // Retrieve the format string and use it to format the value.
            string formatString = parameter as string;
            if (!string.IsNullOrEmpty(formatString))
            {
                return string.Format(formatString, value);
            }

            // If the format string is null or empty, simply
            // call ToString() on the value.
            return value.ToString();
        }

        // No need to implement converting back on a one-way binding
        public object ConvertBack(object value, Type targetType,
            object parameter, string language)
        {
            throw new NotImplementedException();
        }
    }

    public class YesNoValueFormatter : Windows.UI.Xaml.Data.IValueConverter
    {
        // This converts the value object to the string to display.
        // This will work with most simple types.
        public object Convert(object value, Type targetType,
            object parameter, string language)
        {
            // Retrieve the format string and use it to format the value.
            string formatString = parameter as string;
            if (!string.IsNullOrEmpty(formatString))
            {
                return string.Format(formatString, ((bool)value).ToYesNoString());
            }

            // If the format string is null or empty, simply
            // call ToString() on the value.
            return value.ToString();
        }

        // No need to implement converting back on a one-way binding
        public object ConvertBack(object value, Type targetType,
            object parameter, string language)
        {
            throw new NotImplementedException();
        }
    }

    public class VisibleWhenZeroConverter : IValueConverter
    {
        public object Convert(object v, Type t, object p, string l) => Equals(0, (Int32)v) ? Visibility.Visible : Visibility.Collapsed;
        public object ConvertBack(object v, Type t, object p, string l) => null;
    }
}
