using System;
using System.Collections.Specialized;
using System.ComponentModel;
using Windows.UI.Core;

namespace BlueMuse.Helpers
{
    public class ObservableCollection<T> : System.Collections.ObjectModel.ObservableCollection<T>
    {
        //public ObservableCollection() : base()
        //{
        //    this.CollectionChanged += new System.Collections.Specialized.NotifyCollectionChangedEventHandler(ObservableCollection_CollectionChanged);
        //}

        //private void ObservableCollection_CollectionChanged(object sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
        //{
        //    if (e.Action == NotifyCollectionChangedAction.Remove)
        //    {
        //        foreach (T item in e.OldItems)
        //        {
        //            //Removed items
        //            item.PropertyChanged -= EntityViewModelPropertyChanged;
        //        }
        //    }
        //    else if (e.Action == NotifyCollectionChangedAction.Add)
        //    {
        //        foreach (T item in e.NewItems)
        //        {
        //            //Added items
        //            item.PropertyChanged += EntityViewModelPropertyChanged;
        //        }
        //    }
        //}

        //public async void EntityViewModelPropertyChanged(object sender, PropertyChangedEventArgs e)
        //{
        //    await Windows.ApplicationModel.Core.CoreApplication.MainView.CoreWindow.Dispatcher.RunAsync(CoreDispatcherPriority.High,
        //    () =>
        //        {
        //            //This will get called when the property of an object inside the collection changes - note you must make it a 'reset' - dunno why
        //            NotifyCollectionChangedEventArgs args = new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Reset);
        //            OnCollectionChanged(args);
        //        }
        //    );
        //}

        protected async override void OnCollectionChanged(NotifyCollectionChangedEventArgs e)
        { 
            await Windows.ApplicationModel.Core.CoreApplication.MainView.CoreWindow.Dispatcher.RunAsync(CoreDispatcherPriority.High,
            () =>
                {
                    base.OnCollectionChanged(e);
                }
            );
        }

        protected async override void OnPropertyChanged(PropertyChangedEventArgs e)
        {
            await Windows.ApplicationModel.Core.CoreApplication.MainView.CoreWindow.Dispatcher.RunAsync(CoreDispatcherPriority.High,
            () =>
                {
                    base.OnPropertyChanged(e);
                }
            ); 
        }
    }
}
