package edgecomputing_project;

simple BaseStation {
    parameters:        
        double delay;
        double serviceRate;

        bool locallyManaged;

        int queueSize;   

        @signal[responseTimeSignal];
        @statistic[responseTime](source="responseTimeSignal"; record=mean,vector);

        @signal[queueLengthSignal];
        @statistic[queueLength](source="queueLengthSignal"; record=mean,vector);

        @signal[forwardedSignal];
        @statistic[forwarded](source="forwardedSignal"; record=count); 

        @signal[droppedSignal];
        @statistic[dropped](source="droppedSignal"; record=count);
    gates:
        input in @directIn;
}