import time, pylsl
contResolver = pylsl.ContinuousResolver()
inlet = None
myStreamName = 'Muse-00FE (c8:ff:28:30:e6:0c)'
while True:
    streams = contResolver.results()
    stream_names = [si.name() for si in streams]
    print(stream_names)
    if myStreamName in stream_names and inlet is None:
        stream_index = stream_names.index(myStreamName)
        stream = streams[stream_index]
        inlet = pylsl.StreamInlet(stream)
        print('poop1')
    if inlet is not None:
        print('poop2')
        data, sampletimes = inlet.pull_chunk(2)
        print('poop3')
        if len(sampletimes) > 0:
            print(len(sampletimes))
    time.sleep(0.5)
